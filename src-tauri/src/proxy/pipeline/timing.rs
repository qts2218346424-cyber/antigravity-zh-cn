//! X-Timing-* 响应头的唯一拼装点。
//!
//! 四个适配器过去各写 5~7 条 `.header("X-Timing-...")`，字段与格式容易漂移。
//! 这里保留一个数据结构 + `Builder` 扩展，适配器只负责填入已算好的毫秒值。

use axum::http::response::Builder;
use std::sync::{Arc, OnceLock};

/// 供流式链路跨阶段共享生效端点首块 TTFT（毫秒）的容器。
///
/// 流式发头时由于首个 Token 尚未到达，HTTP 响应头只能写入 -1（未知）；
/// 当首个非心跳数据块到达并触发 probe 时，测得的真实端点 TTFT 写入该容器；
/// monitor_middleware 在流结束后即可读取该真实值并回填日志，
/// 消除日志中遗留 -1.0 占位符、以及前端显示 -0.0010s 负数的问题。
#[derive(Clone, Default, Debug)]
pub struct StreamTtftCapture(pub Arc<OnceLock<f64>>);

impl StreamTtftCapture {
    pub fn new() -> Self {
        Self(Arc::new(OnceLock::new()))
    }

    pub fn set(&self, ttft_ms: f64) {
        let _ = self.0.set(ttft_ms);
    }

    pub fn get(&self) -> Option<f64> {
        self.0.get().copied()
    }
}

#[derive(Debug, Clone, Default)]
pub struct TimingHeaders {
    pub clean_ms: f64,
    pub norm_ms: f64,
    pub thinking_ms: f64,
    /// 单源 TTFT 口径：首个上游数据块；流式发头时写 -1。
    pub ttft_ms: f64,
    /// 响应头到达耗时；与 TTFT 分开表达，不互相冒充。
    pub headers_ms: f64,
    pub ttft_overhead_ms: f64,
    pub ttft_attempts: String,
}

impl TimingHeaders {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        clean_ms: f64,
        norm_ms: f64,
        thinking_ms: f64,
        ttft_ms: f64,
        headers_ms: f64,
        ttft_overhead_ms: f64,
        ttft_attempts: &str,
    ) -> Self {
        Self {
            clean_ms,
            norm_ms,
            thinking_ms,
            ttft_ms,
            headers_ms,
            ttft_overhead_ms,
            ttft_attempts: ttft_attempts.to_string(),
        }
    }
}

pub trait TimingBuilderExt {
    /// 写入完整的 7 个 X-Timing 头（成功响应）。
    fn timing(self, headers: &TimingHeaders) -> Self;
    /// 写入 5 个核心头 + overhead（早期错误响应）。
    fn timing_overhead(self, headers: &TimingHeaders) -> Self;
    /// 写入核心 5 个 X-Timing 头（错误/降级响应，不伪造 overhead/attempts）。
    fn timing_core(self, headers: &TimingHeaders) -> Self;
    /// 附带挂载流式 TTFT 捕获器到 response extensions
    fn timing_stream(self, headers: &TimingHeaders, capture: StreamTtftCapture) -> Self;
}

impl TimingBuilderExt for Builder {
    fn timing(self, h: &TimingHeaders) -> Self {
        self.timing_core(h)
            .header(
                "X-Timing-Ttft-Overhead-Ms",
                format!("{:.3}", h.ttft_overhead_ms),
            )
            .header("X-Timing-Ttft-Attempts", h.ttft_attempts.as_str())
    }

    fn timing_overhead(self, h: &TimingHeaders) -> Self {
        self.timing_core(h).header(
            "X-Timing-Ttft-Overhead-Ms",
            format!("{:.3}", h.ttft_overhead_ms),
        )
    }

    fn timing_core(self, h: &TimingHeaders) -> Self {
        self.header("X-Timing-Clean-Ms", format!("{:.3}", h.clean_ms))
            .header("X-Timing-Norm-Ms", format!("{:.3}", h.norm_ms))
            .header("X-Timing-Thinking-Ms", format!("{:.3}", h.thinking_ms))
            .header("X-Timing-Ttft-Ms", format!("{:.3}", h.ttft_ms))
            .header("X-Timing-Headers-Ms", format!("{:.3}", h.headers_ms))
    }

    fn timing_stream(self, headers: &TimingHeaders, capture: StreamTtftCapture) -> Self {
        self.timing(headers).extension(capture)
    }
}
