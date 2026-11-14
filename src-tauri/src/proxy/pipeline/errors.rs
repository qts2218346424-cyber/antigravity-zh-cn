//! 协议无关的上游错误解析工具。

/// 判定是否属于偶发性/瞬态 Token 获取错误（例如超时、锁争抢、系统繁忙）
pub fn is_transient_token_error(err: &str) -> bool {
    let lower = err.to_ascii_lowercase();
    lower.contains("timeout") || lower.contains("too busy") || lower.contains("deadlock")
}

/// 深度解析、剥离前缀与反转义上游错误，返回 (上游原始纯文本消息, 结构化解析对象)
pub fn parse_raw_upstream_error(error_text: &str) -> (String, serde_json::Value) {
    let trimmed = error_text.trim();
    // 1. 剥离可能附带的外层 HTTP 前缀，如 "HTTP 400: "、"HTTP 500: "、"All accounts exhausted. Last error: "
    let clean_str = if let Some(pos) = trimmed.find("HTTP ") {
        if let Some(colon_pos) = trimmed[pos..].find(": ") {
            trimmed[pos + colon_pos + 2..].trim()
        } else {
            trimmed
        }
    } else if let Some(stripped) = trimmed.strip_prefix("All accounts exhausted. Last error: ") {
        stripped.trim()
    } else {
        trimmed
    };

    // 2. 深度递归反转义解析 JSON
    let mut current_val: Option<serde_json::Value> = serde_json::from_str(clean_str).ok();
    // 如果解析出来的还是 string 且看起来像 JSON，尝试二次/三次解析（处理被双重转义的情况）
    for _ in 0..3 {
        if let Some(serde_json::Value::String(ref s)) = current_val {
            let s_trim = s.trim();
            if (s_trim.starts_with('{') && s_trim.ends_with('}'))
                || (s_trim.starts_with('[') && s_trim.ends_with(']'))
            {
                if let Ok(nested) = serde_json::from_str(s_trim) {
                    current_val = Some(nested);
                    continue;
                }
            }
        }
        break;
    }

    // 3. 如果当前值是个 Object，且它某个字段（例如 "response" 或 "raw"）又是嵌套 JSON 字符串，递归解析内部
    if let Some(mut parsed) = current_val {
        if let Some(obj) = parsed.as_object_mut() {
            for key in ["response", "raw", "error", "details", "message"] {
                if let Some(serde_json::Value::String(s)) = obj.get(key) {
                    let s_trim = s.trim();
                    if (s_trim.starts_with('{') && s_trim.ends_with('}'))
                        || (s_trim.starts_with('[') && s_trim.ends_with(']'))
                    {
                        if let Ok(nested) = serde_json::from_str::<serde_json::Value>(s_trim) {
                            obj.insert(key.to_string(), nested);
                        }
                    }
                }
            }
        }

        // 从结构化对象中提取原生的 message
        let raw_msg = if let Some(err_obj) = parsed.get("error") {
            if let Some(msg) = err_obj.get("message").and_then(|m| m.as_str()) {
                msg.to_string()
            } else if let Some(msg) = err_obj.as_str() {
                msg.to_string()
            } else {
                clean_str.to_string()
            }
        } else if let Some(msg) = parsed.get("message").and_then(|m| m.as_str()) {
            msg.to_string()
        } else if let Some(msg) = parsed.get("detail").and_then(|m| m.as_str()) {
            msg.to_string()
        } else {
            clean_str.to_string()
        };

        (raw_msg, parsed)
    } else {
        (
            clean_str.to_string(),
            serde_json::json!({ "raw": clean_str }),
        )
    }
}
