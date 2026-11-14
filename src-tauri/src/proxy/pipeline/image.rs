use reqwest::StatusCode;
use serde_json::Value;

/// 检查上游 Gemini 协议响应中是否包含非空的合法图片数据 (inlineData / inline_data)
pub fn response_has_inline_image_data(value: &Value) -> bool {
    let response = value.get("response").unwrap_or(value);
    response
        .get("candidates")
        .and_then(Value::as_array)
        .is_some_and(|candidates| {
            candidates.iter().any(|candidate| {
                candidate
                    .get("content")
                    .and_then(|content| content.get("parts"))
                    .and_then(Value::as_array)
                    .is_some_and(|parts| {
                        parts.iter().any(|part| {
                            part.get("inlineData")
                                .or_else(|| part.get("inline_data"))
                                .and_then(|image| image.get("data"))
                                .and_then(Value::as_str)
                                .is_some_and(|data| !data.is_empty())
                        })
                    })
            })
        })
}

/// [Fixes #3756] 上游虽返回 HTTP 200 但未包含有效图片时的脱敏诊断结果与状态码分类
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ImageDiagnostic {
    pub status: StatusCode,
    pub is_safety_or_policy: bool,
    pub message: String,
    pub block_reason: Option<String>,
    pub finish_reason: Option<String>,
    pub refusal_text: Option<String>,
}

/// [Fixes #3756] 从上游 Gemini 协议响应中深度提取脱敏诊断原因与对应状态码
pub fn extract_image_generation_diagnostic(json: &Value) -> ImageDiagnostic {
    let raw = json.get("response").unwrap_or(json);

    // 1. 检查上游是否在 200 中包裹了错误对象
    if let Some(err_obj) = raw.get("error").or_else(|| json.get("error")) {
        if let Some(msg) = err_obj.get("message").and_then(Value::as_str) {
            return ImageDiagnostic {
                status: StatusCode::BAD_GATEWAY,
                is_safety_or_policy: false,
                message: format!("Upstream API error: {}", msg),
                block_reason: None,
                finish_reason: None,
                refusal_text: None,
            };
        }
    }

    // 2. 检查 promptFeedback (提示词级别安全/策略拦截)
    if let Some(feedback) = raw.get("promptFeedback") {
        let block_reason = feedback
            .get("blockReason")
            .and_then(Value::as_str)
            .unwrap_or("SAFETY")
            .to_string();
        return ImageDiagnostic {
            status: StatusCode::BAD_REQUEST,
            is_safety_or_policy: true,
            message: format!(
                "Prompt blocked by upstream safety policy (blockReason: {})",
                block_reason
            ),
            block_reason: Some(block_reason),
            finish_reason: None,
            refusal_text: None,
        };
    }

    // 3. 检查 candidates
    if let Some(candidates) = raw.get("candidates").and_then(Value::as_array) {
        if candidates.is_empty() {
            return ImageDiagnostic {
                status: StatusCode::BAD_GATEWAY,
                is_safety_or_policy: false,
                message: "Upstream returned empty candidates array".to_string(),
                block_reason: None,
                finish_reason: None,
                refusal_text: None,
            };
        }

        if let Some(cand) = candidates.first() {
            // 检查 candidate 级别的 finishReason
            let finish_reason = cand.get("finishReason").and_then(Value::as_str);
            if let Some(fr) = finish_reason {
                let fr_upper = fr.to_ascii_uppercase();
                if fr_upper == "SAFETY"
                    || fr_upper == "BLOCKLIST"
                    || fr_upper == "PROHIBITED_CONTENT"
                    || fr_upper == "SPII"
                {
                    return ImageDiagnostic {
                        status: StatusCode::BAD_REQUEST,
                        is_safety_or_policy: true,
                        message: format!(
                            "Image generation blocked by safety policy (finishReason: {})",
                            fr
                        ),
                        block_reason: None,
                        finish_reason: Some(fr.to_string()),
                        refusal_text: None,
                    };
                }
            }

            // 检查 content.parts 是否包含文本拒答或解释说明
            if let Some(parts) = cand
                .get("content")
                .and_then(|c| c.get("parts"))
                .and_then(Value::as_array)
            {
                let mut text_parts = Vec::new();
                for p in parts {
                    if let Some(txt) = p.get("text").and_then(Value::as_str) {
                        let trimmed = txt.trim();
                        if !trimmed.is_empty() {
                            text_parts.push(trimmed);
                        }
                    }
                }
                if !text_parts.is_empty() {
                    let refusal_text = text_parts.join(" ");
                    let truncated =
                        crate::proxy::mappers::common_utils::safe_truncate_str(&refusal_text, 250);
                    return ImageDiagnostic {
                        status: StatusCode::BAD_REQUEST,
                        is_safety_or_policy: true,
                        message: format!("Upstream model refused to generate image: {}", truncated),
                        block_reason: None,
                        finish_reason: finish_reason.map(str::to_string),
                        refusal_text: Some(truncated.to_string()),
                    };
                }
            }

            if let Some(fr) = finish_reason {
                return ImageDiagnostic {
                    status: StatusCode::BAD_GATEWAY,
                    is_safety_or_policy: false,
                    message: format!(
                        "Upstream returned candidate without image data (finishReason: {})",
                        fr
                    ),
                    block_reason: None,
                    finish_reason: Some(fr.to_string()),
                    refusal_text: None,
                };
            }
        }
    }

    ImageDiagnostic {
        status: StatusCode::BAD_GATEWAY,
        is_safety_or_policy: false,
        message: "Upstream returned 200 OK but response contains no valid image data".to_string(),
        block_reason: None,
        finish_reason: None,
        refusal_text: None,
    }
}

/// 检查文本中是否包含非空的 data:image/... base64 URL
pub fn text_has_nonempty_image_data_url(text: &str) -> bool {
    let mut remaining = text;
    while let Some(start) = remaining.find("data:image/") {
        let candidate = &remaining[start..];
        if let Some((_, encoded)) = candidate.split_once(";base64,") {
            if encoded.chars().next().is_some_and(|first| {
                !first.is_whitespace() && !matches!(first, '"' | '\\' | ')' | ']' | '}')
            }) {
                return true;
            }
        }
        remaining = &candidate["data:image/".len()..];
    }
    false
}

/// 递归检查 JSON 结构中是否存在非空的 data:image/... base64 URL
pub fn value_has_nonempty_image_data_url(value: &Value) -> bool {
    match value {
        Value::String(text) => text_has_nonempty_image_data_url(text),
        Value::Array(values) => values.iter().any(value_has_nonempty_image_data_url),
        Value::Object(values) => values.values().any(value_has_nonempty_image_data_url),
        _ => false,
    }
}

/// 检查 SSE 流式分块中是否包含非空的图片数据 URL
pub fn stream_chunk_has_image_data(bytes: &[u8]) -> bool {
    String::from_utf8_lossy(bytes).lines().any(|line| {
        let Some(data) = line.trim_start().strip_prefix("data:") else {
            return false;
        };
        serde_json::from_str::<Value>(data.trim())
            .ok()
            .is_some_and(|payload| value_has_nonempty_image_data_url(&payload))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_response_has_inline_image_data() {
        let empty = json!({
            "response": {"candidates": [{"content": {"parts": [{"inlineData": {"data": ""}}]}}]}
        });
        let image = json!({
            "response": {"candidates": [{"content": {"parts": [{"inlineData": {"data": "AQ=="}}]}}]}
        });
        assert!(!response_has_inline_image_data(&empty));
        assert!(response_has_inline_image_data(&image));
    }

    #[test]
    fn test_extract_image_generation_diagnostic() {
        // 1. promptFeedback 安全策略拦截
        let prompt_feedback = json!({
            "promptFeedback": {
                "blockReason": "SAFETY"
            }
        });
        let diag = extract_image_generation_diagnostic(&prompt_feedback);
        assert_eq!(diag.status, StatusCode::BAD_REQUEST);
        assert!(diag.is_safety_or_policy);
        assert!(diag.message.contains("blockReason: SAFETY"));
        assert_eq!(diag.block_reason.as_deref(), Some("SAFETY"));

        // 2. candidate finishReason 安全策略拦截
        let cand_safety = json!({
            "candidates": [{
                "finishReason": "SAFETY"
            }]
        });
        let diag = extract_image_generation_diagnostic(&cand_safety);
        assert_eq!(diag.status, StatusCode::BAD_REQUEST);
        assert!(diag.is_safety_or_policy);
        assert!(diag.message.contains("finishReason: SAFETY"));
        assert_eq!(diag.finish_reason.as_deref(), Some("SAFETY"));

        // 3. candidate 文本拒答部件
        let text_refusal = json!({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "I cannot create images of real people."
                    }]
                },
                "finishReason": "STOP"
            }]
        });
        let diag = extract_image_generation_diagnostic(&text_refusal);
        assert_eq!(diag.status, StatusCode::BAD_REQUEST);
        assert!(diag.is_safety_or_policy);
        assert!(diag
            .message
            .contains("I cannot create images of real people."));
        assert!(diag.refusal_text.is_some());

        // 4. 空候选集
        let empty_cand = json!({
            "candidates": []
        });
        let diag = extract_image_generation_diagnostic(&empty_cand);
        assert_eq!(diag.status, StatusCode::BAD_GATEWAY);
        assert!(!diag.is_safety_or_policy);
        assert!(diag.message.contains("empty candidates array"));

        // 5. 嵌套 upstream error
        let upstream_err = json!({
            "error": {
                "message": "Resource exhausted"
            }
        });
        let diag = extract_image_generation_diagnostic(&upstream_err);
        assert_eq!(diag.status, StatusCode::BAD_GATEWAY);
        assert!(!diag.is_safety_or_policy);
        assert!(diag.message.contains("Resource exhausted"));
    }
}
