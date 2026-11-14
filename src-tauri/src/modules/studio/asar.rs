use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub const ASAR_INTEGRITY_BLOCK_SIZE: usize = 4 * 1024 * 1024;

fn align4(size: usize) -> usize {
    (size + 3) & !3
}

fn hex_encode(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

/// 计算 ASAR 4MB 分块及全文 SHA-256 完整性结构
pub fn calculate_file_integrity(data: &[u8]) -> Value {
    let mut blocks = Vec::new();
    if data.is_empty() {
        let mut hasher = Sha256::new();
        hasher.update(data);
        blocks.push(Value::String(hex_encode(&hasher.finalize())));
    } else {
        for chunk in data.chunks(ASAR_INTEGRITY_BLOCK_SIZE) {
            let mut hasher = Sha256::new();
            hasher.update(chunk);
            blocks.push(Value::String(hex_encode(&hasher.finalize())));
        }
    }

    let mut full_hasher = Sha256::new();
    full_hasher.update(data);
    let full_hash = hex_encode(&full_hasher.finalize());

    json!({
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": ASAR_INTEGRITY_BLOCK_SIZE,
        "blocks": blocks,
    })
}

/// 解析 ASAR 二进制头，返回 `(header_size, header_json_str, header_value)`
pub fn read_asar_header(data: &[u8]) -> Result<(usize, String, Value), String> {
    if data.len() < 16 {
        return Err("ASAR 文件损坏或格式不支持（小于 16 字节）".to_string());
    }
    let header_size = u32::from_le_bytes([data[4], data[5], data[6], data[7]]) as usize;
    if 8 + header_size > data.len() || header_size < 8 {
        return Err(format!(
            "ASAR header_size 非法: {} (总长度 {})",
            header_size,
            data.len()
        ));
    }
    let header_pickle = &data[8..8 + header_size];
    let header_str_size = i32::from_le_bytes([
        header_pickle[4],
        header_pickle[5],
        header_pickle[6],
        header_pickle[7],
    ]);
    if header_str_size < 0 || 8 + (header_str_size as usize) > header_pickle.len() {
        return Err(format!("ASAR header_str_size 非法: {}", header_str_size));
    }
    let header_str = std::str::from_utf8(&header_pickle[8..8 + header_str_size as usize])
        .map_err(|e| format!("ASAR 头 UTF-8 解码失败: {}", e))?
        .to_string();
    let header: Value =
        serde_json::from_str(&header_str).map_err(|e| format!("ASAR 头 JSON 解析失败: {}", e))?;
    Ok((header_size, header_str, header))
}

/// 将更新后的 JSON 字符串重新编码为 4 字节对齐的 Chromium Pickle ASAR 头
pub fn encode_asar_header_dynamic(header_string: &str) -> Vec<u8> {
    let hb = header_string.as_bytes();
    let payload_size = align4(4 + hb.len());
    let pad_len = payload_size - 4 - hb.len();

    let mut pickle = Vec::with_capacity(4 + payload_size);
    pickle.extend_from_slice(&(payload_size as u32).to_le_bytes());
    pickle.extend_from_slice(&(hb.len() as i32).to_le_bytes());
    pickle.extend_from_slice(hb);
    pickle.resize(pickle.len() + pad_len, 0u8);

    let mut header = Vec::with_capacity(8 + pickle.len());
    header.extend_from_slice(&4u32.to_le_bytes());
    header.extend_from_slice(&(pickle.len() as u32).to_le_bytes());
    header.extend_from_slice(&pickle);
    header
}

fn get_asar_file_entry<'a>(header: &'a Value, file_path: &str) -> Result<&'a Value, String> {
    let mut node = header;
    for part in file_path.split('/') {
        if part.is_empty() {
            continue;
        }
        let files = node
            .get("files")
            .and_then(|v| v.as_object())
            .ok_or_else(|| format!("ASAR 索引中未找到目录节点: {}", file_path))?;
        node = files
            .get(part)
            .ok_or_else(|| format!("ASAR 索引中未找到文件: {}", file_path))?;
    }
    if node.get("offset").is_none() || node.get("size").is_none() {
        return Err(format!("文件条目缺少 offset 或 size 字段: {}", file_path));
    }
    Ok(node)
}

fn get_asar_file_entry_mut<'a>(
    header: &'a mut Value,
    file_path: &str,
) -> Result<&'a mut Value, String> {
    let mut node = header;
    for part in file_path.split('/') {
        if part.is_empty() {
            continue;
        }
        let files = node
            .get_mut("files")
            .and_then(|v| v.as_object_mut())
            .ok_or_else(|| format!("ASAR 索引中未找到目录节点: {}", file_path))?;
        node = files
            .get_mut(part)
            .ok_or_else(|| format!("ASAR 索引中未找到文件: {}", file_path))?;
    }
    Ok(node)
}

fn parse_entry_offset(entry: &Value) -> Result<usize, String> {
    if let Some(s) = entry.get("offset").and_then(|v| v.as_str()) {
        s.parse::<usize>()
            .map_err(|e| format!("ASAR offset 字符串解析失败 ({}): {}", s, e))
    } else if let Some(n) = entry.get("offset").and_then(|v| v.as_u64()) {
        Ok(n as usize)
    } else {
        Err("ASAR 条目缺少合法 offset".to_string())
    }
}

fn parse_entry_size(entry: &Value) -> Result<usize, String> {
    if let Some(n) = entry.get("size").and_then(|v| v.as_u64()) {
        Ok(n as usize)
    } else if let Some(s) = entry.get("size").and_then(|v| v.as_str()) {
        s.parse::<usize>()
            .map_err(|e| format!("ASAR size 字符串解析失败 ({}): {}", s, e))
    } else {
        Err("ASAR 条目缺少合法 size".to_string())
    }
}

/// 从 ASAR 二进制字节读取指定内部文件的内容
pub fn read_asar_file_content(asar_data: &[u8], file_path: &str) -> Result<Vec<u8>, String> {
    let (header_size, _, header) = read_asar_header(asar_data)?;
    let entry = get_asar_file_entry(&header, file_path)?;
    let offset = 8 + header_size + parse_entry_offset(entry)?;
    let size = parse_entry_size(entry)?;
    if offset + size > asar_data.len() {
        return Err(format!(
            "ASAR 读取越界: {} (offset={}, size={}, total={})",
            file_path,
            offset,
            size,
            asar_data.len()
        ));
    }
    Ok(asar_data[offset..offset + size].to_vec())
}

fn shift_offsets_after(
    node: &mut Value,
    current_path: &str,
    target_path: &str,
    old_offset: usize,
    delta: isize,
) {
    let Some(files) = node.get_mut("files").and_then(|v| v.as_object_mut()) else {
        return;
    };
    for (name, child) in files.iter_mut() {
        let child_path = if current_path.is_empty() {
            name.clone()
        } else {
            format!("{}/{}", current_path, name)
        };
        if child.get("files").is_some() {
            shift_offsets_after(child, &child_path, target_path, old_offset, delta);
        } else if child_path != target_path {
            if let Ok(other_off) = parse_entry_offset(child) {
                if other_off > old_offset {
                    let new_off = (other_off as isize + delta) as u64;
                    if let Some(obj) = child.as_object_mut() {
                        // Electron ASAR 规范要求文件 offset 为十进制字符串
                        obj.insert("offset".to_string(), Value::String(new_off.to_string()));
                    }
                }
            }
        }
    }
}

/// 原位替换 ASAR 归档内部特定文件的内容，并动态更新偏移量与头部哈希。
/// 100% 保留 `unpacked: true` 的外部文件索引 (`app.asar.unpacked/`)。
pub fn replace_asar_file_content(
    asar_data: &mut Vec<u8>,
    file_path: &str,
    new_content: &[u8],
) -> Result<(), String> {
    let (header_size, _, mut header) = read_asar_header(asar_data)?;
    let (old_offset, old_size) = {
        let entry = get_asar_file_entry(&header, file_path)?;
        (parse_entry_offset(entry)?, parse_entry_size(entry)?)
    };

    let content_offset = 8 + header_size + old_offset;
    let content_end = content_offset + old_size;
    if content_end > asar_data.len() {
        return Err(format!(
            "ASAR 目标文件偏移越界: {} (end={}, total={})",
            file_path,
            content_end,
            asar_data.len()
        ));
    }

    if &asar_data[content_offset..content_end] == new_content {
        return Ok(());
    }

    let delta = new_content.len() as isize - old_size as isize;
    let normalized_target = file_path.trim_matches('/');

    {
        let entry_mut = get_asar_file_entry_mut(&mut header, file_path)?;
        let obj = entry_mut
            .as_object_mut()
            .ok_or_else(|| format!("ASAR 条目不是 JSON 对象: {}", file_path))?;
        obj.insert("size".to_string(), json!(new_content.len() as u64));
        if obj.contains_key("integrity") {
            obj.insert(
                "integrity".to_string(),
                calculate_file_integrity(new_content),
            );
        }
    }

    if delta != 0 {
        shift_offsets_after(&mut header, "", normalized_target, old_offset, delta);
    }

    let updated_header_string =
        serde_json::to_string(&header).map_err(|e| format!("序列化 ASAR 头失败: {}", e))?;
    let updated_header = encode_asar_header_dynamic(&updated_header_string);

    let body_start = 8 + header_size;
    let rel_start = old_offset;
    let rel_end = old_offset + old_size;
    let body = &asar_data[body_start..];

    let mut rebuilt = Vec::with_capacity(
        updated_header.len() + (body.len() as isize + delta) as usize,
    );
    rebuilt.extend_from_slice(&updated_header);
    rebuilt.extend_from_slice(&body[..rel_start]);
    rebuilt.extend_from_slice(new_content);
    rebuilt.extend_from_slice(&body[rel_end..]);

    *asar_data = rebuilt;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn build_mock_asar(files: &[(&str, &[u8])]) -> Vec<u8> {
        let mut root = json!({ "files": {} });
        let mut body = Vec::new();
        for (name, content) in files {
            let off = body.len();
            body.extend_from_slice(content);
            root["files"][*name] = json!({
                "size": content.len(),
                "offset": off.to_string(),
                "integrity": calculate_file_integrity(content),
            });
        }
        // 加入一个 unpacked 条目验证不会被破坏
        root["files"]["native.node"] = json!({
            "size": 123,
            "unpacked": true
        });
        let header_str = serde_json::to_string(&root).unwrap();
        let mut out = encode_asar_header_dynamic(&header_str);
        out.extend_from_slice(&body);
        out
    }

    #[test]
    fn test_read_and_replace_asar_preserves_offsets_and_unpacked() {
        let mut archive = build_mock_asar(&[
            ("a.js", b"console.log('a');"),
            ("b.js", b"console.log('bb');"),
            ("c.js", b"console.log('ccc');"),
        ]);

        assert_eq!(read_asar_file_content(&archive, "a.js").unwrap(), b"console.log('a');");
        assert_eq!(read_asar_file_content(&archive, "b.js").unwrap(), b"console.log('bb');");

        let replacement = b"console.log('replaced-longer-payload-for-b');";
        replace_asar_file_content(&mut archive, "b.js", replacement).unwrap();

        assert_eq!(read_asar_file_content(&archive, "a.js").unwrap(), b"console.log('a');");
        assert_eq!(read_asar_file_content(&archive, "b.js").unwrap(), replacement);
        assert_eq!(read_asar_file_content(&archive, "c.js").unwrap(), b"console.log('ccc');");

        let (_, _, header) = read_asar_header(&archive).unwrap();
        assert_eq!(header["files"]["native.node"]["unpacked"], json!(true));
        assert!(header["files"]["c.js"]["offset"].is_string());
    }
}
