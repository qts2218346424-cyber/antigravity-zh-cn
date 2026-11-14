import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import {
    Brain,
    MessageSquare,
    Wrench,
    Copy,
    Check,
    ChevronDown,
    ChevronRight,
    User,
    Bot,
    Terminal,
    Sparkles,
    Search,
    Cpu
} from 'lucide-react';
import { copyToClipboard } from '../../utils/clipboard';

export interface StructuredMessage {
    role: 'system' | 'user' | 'assistant' | 'tool' | 'other';
    roleLabel: string;
    text?: string;
    thinking?: string;
    thinkingSignature?: string;
    toolCalls?: Array<{
        id?: string;
        name: string;
        args?: any;
    }>;
    toolResult?: {
        name?: string;
        callId?: string;
        result?: any;
    };
    raw?: any;
}

export interface StructuredTool {
    name: string;
    description?: string;
    parameters?: any;
}

export interface StructuredConfig {
    model?: string;
    maxTokens?: number;
    temperature?: number;
    thinkingBudget?: number | string;
    includeThoughts?: boolean;
    sessionId?: string;
    requestId?: string;
    extra?: Record<string, any>;
}

export interface StructuredPayloadData {
    isStructured: boolean;
    systemPrompt?: string;
    messages: StructuredMessage[];
    tools: StructuredTool[];
    config: StructuredConfig;
    usage?: {
        inputTokens?: number;
        outputTokens?: number;
        cachedTokens?: number | null;
        totalTokens?: number;
    };
}

/**
 * 智能解析大模型请求或响应 JSON，适配 Gemini, Claude, OpenAI, Antigravity 各种格式
 */
export function parsePayloadToStructured(rawJsonText: string, isResponse: boolean = false): StructuredPayloadData | null {
    if (!rawJsonText || typeof rawJsonText !== 'string') return null;

    let obj: any;
    try {
        obj = JSON.parse(rawJsonText);
    } catch {
        return null;
    }

    if (!obj || typeof obj !== 'object') return null;

    const data: StructuredPayloadData = {
        isStructured: false,
        messages: [],
        tools: [],
        config: {},
    };

    // 0. 模型与生成配置解析
    if (obj.model) data.config.model = String(obj.model);
    if (obj.requestId) data.config.requestId = String(obj.requestId);
    if (obj.sessionId || obj.session_id) data.config.sessionId = String(obj.sessionId || obj.session_id);

    const genCfg = obj.generationConfig || obj.generation_config || {};
    if (genCfg.maxOutputTokens || obj.max_tokens || obj.maxOutputTokens) {
        data.config.maxTokens = genCfg.maxOutputTokens || obj.max_tokens || obj.maxOutputTokens;
    }
    if (genCfg.temperature !== undefined || obj.temperature !== undefined) {
        data.config.temperature = genCfg.temperature ?? obj.temperature;
    }
    if (genCfg.thinkingConfig || obj.thinking || obj.thinkingConfig) {
        const tc = genCfg.thinkingConfig || obj.thinkingConfig || obj.thinking || {};
        data.config.includeThoughts = tc.includeThoughts !== undefined ? Boolean(tc.includeThoughts) : (tc.type === 'enabled' || tc.type === 'adaptive');
        data.config.thinkingBudget = tc.thinkingBudget ?? tc.budget_tokens;
    }

    // 1. 系统提示词 (System Prompt) 提取
    // Gemini: systemInstruction
    if (obj.systemInstruction || obj.system_instruction) {
        const sys = obj.systemInstruction || obj.system_instruction;
        if (typeof sys === 'string') {
            data.systemPrompt = sys;
        } else if (Array.isArray(sys.parts)) {
            data.systemPrompt = sys.parts.map((p: any) => p?.text || '').filter(Boolean).join('\n');
        } else if (typeof sys.text === 'string') {
            data.systemPrompt = sys.text;
        }
    }
    // Claude: system
    if (!data.systemPrompt && obj.system) {
        if (typeof obj.system === 'string') {
            data.systemPrompt = obj.system;
        } else if (Array.isArray(obj.system)) {
            data.systemPrompt = obj.system.map((item: any) => item?.text || '').filter(Boolean).join('\n');
        }
    }
    // OpenAI: messages 中 role === 'system' or 'developer'
    if (Array.isArray(obj.messages)) {
        const sysMsgs = obj.messages.filter((m: any) => m?.role === 'system' || m?.role === 'developer');
        if (!data.systemPrompt && sysMsgs.length > 0) {
            data.systemPrompt = sysMsgs.map((m: any) => {
                if (typeof m.content === 'string') return m.content;
                if (Array.isArray(m.content)) return m.content.map((c: any) => c?.text || '').join('');
                return '';
            }).filter(Boolean).join('\n\n');
        }
    }

    // 2. 工具声明 (Tools) 提取
    if (Array.isArray(obj.tools)) {
        obj.tools.forEach((t: any) => {
            // Gemini: { functionDeclarations: [...] }
            if (Array.isArray(t.functionDeclarations)) {
                t.functionDeclarations.forEach((fd: any) => {
                    data.tools.push({
                        name: fd.name || 'unnamed_function',
                        description: fd.description,
                        parameters: fd.parameters,
                    });
                });
            }
            // Claude: { name, description, input_schema }
            else if (t.name) {
                data.tools.push({
                    name: t.name,
                    description: t.description,
                    parameters: t.input_schema,
                });
            }
            // OpenAI: { type: 'function', function: { name, description, parameters } }
            else if (t.type === 'function' && t.function) {
                data.tools.push({
                    name: t.function.name || 'unnamed_function',
                    description: t.function.description,
                    parameters: t.function.parameters,
                });
            }
        });
    }

    // 3. 对话消息 (Messages / Contents) 提取
    // Gemini: contents
    if (Array.isArray(obj.contents)) {
        obj.contents.forEach((c: any) => {
            const role = c.role === 'model' ? 'assistant' : c.role === 'user' ? 'user' : 'other';
            let text = '';
            let thinking = '';
            let thinkingSignature = '';
            const toolCalls: any[] = [];
            let toolResult: any = undefined;

            if (Array.isArray(c.parts)) {
                c.parts.forEach((p: any) => {
                    if (p.text) {
                        text += (text ? '\n' : '') + p.text;
                    }
                    if (p.thought) {
                        thinking += (thinking ? '\n' : '') + p.thought;
                    }
                    if (p.thoughtSignature || p.thought_signature) {
                        thinkingSignature = p.thoughtSignature || p.thought_signature;
                    }
                    if (p.functionCall) {
                        toolCalls.push({
                            name: p.functionCall.name,
                            args: p.functionCall.args,
                        });
                    }
                    if (p.functionResponse) {
                        toolResult = {
                            name: p.functionResponse.name,
                            result: p.functionResponse.response,
                        };
                    }
                });
            }

            data.messages.push({
                role: toolResult ? 'tool' : (role as any),
                roleLabel: toolResult ? 'Tool Response' : (role === 'assistant' ? 'Model (Assistant)' : 'User'),
                text: text || undefined,
                thinking: thinking || undefined,
                thinkingSignature: thinkingSignature || undefined,
                toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
                toolResult,
                raw: c,
            });
        });
    }
    // OpenAI / Claude: messages
    else if (Array.isArray(obj.messages)) {
        obj.messages.forEach((m: any) => {
            // 跳过已提成 system prompt 的系统消息
            if (m.role === 'system' || m.role === 'developer') return;

            const role = m.role === 'assistant' ? 'assistant' : m.role === 'user' ? 'user' : m.role === 'tool' ? 'tool' : 'other';
            let text = '';
            let thinking = '';
            let thinkingSignature = '';
            const toolCalls: any[] = [];
            let toolResult: any = undefined;

            // Claude 格式
            if (Array.isArray(m.content)) {
                m.content.forEach((block: any) => {
                    if (block.type === 'text') text += (text ? '\n' : '') + (block.text || '');
                    if (block.type === 'thinking') {
                        thinking += (thinking ? '\n' : '') + (block.thinking || '');
                        if (block.signature) thinkingSignature = block.signature;
                    }
                    if (block.type === 'tool_use') {
                        toolCalls.push({
                            id: block.id,
                            name: block.name,
                            args: block.input,
                        });
                    }
                    if (block.type === 'tool_result') {
                        toolResult = {
                            callId: block.tool_use_id,
                            result: typeof block.content === 'string' ? block.content : block.content,
                        };
                    }
                });
            } else if (typeof m.content === 'string') {
                text = m.content;
            }

            // OpenAI tool_calls
            if (Array.isArray(m.tool_calls)) {
                m.tool_calls.forEach((tc: any) => {
                    toolCalls.push({
                        id: tc.id,
                        name: tc.function?.name,
                        args: tc.function?.arguments,
                    });
                });
            }

            if (m.role === 'tool') {
                toolResult = {
                    callId: m.tool_call_id,
                    result: m.content,
                };
            }

            data.messages.push({
                role: (toolResult ? 'tool' : role) as any,
                roleLabel: toolResult ? 'Tool Result' : (role === 'assistant' ? 'Assistant' : 'User'),
                text: text || undefined,
                thinking: thinking || undefined,
                thinkingSignature: thinkingSignature || undefined,
                toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
                toolResult,
                raw: m,
            });
        });
    }

    // 4. 如果是 Response 格式提取 (Gemini candidates / Claude content / OpenAI choices)
    if (isResponse || obj.candidates || obj.choices || obj.content) {
        // Gemini: candidates
        if (Array.isArray(obj.candidates) && obj.candidates.length > 0) {
            const cand = obj.candidates[0];
            if (cand?.content) {
                let text = '';
                let thinking = '';
                let thinkingSignature = '';
                const toolCalls: any[] = [];

                if (Array.isArray(cand.content.parts)) {
                    cand.content.parts.forEach((p: any) => {
                        if (p.text) text += (text ? '\n' : '') + p.text;
                        if (p.thought) thinking += (thinking ? '\n' : '') + p.thought;
                        if (p.thoughtSignature || p.thought_signature) {
                            thinkingSignature = p.thoughtSignature || p.thought_signature;
                        }
                        if (p.functionCall) {
                            toolCalls.push({
                                name: p.functionCall.name,
                                args: p.functionCall.args,
                            });
                        }
                    });
                }

                data.messages.push({
                    role: 'assistant',
                    roleLabel: 'Assistant Response',
                    text: text || undefined,
                    thinking: thinking || undefined,
                    thinkingSignature: thinkingSignature || undefined,
                    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
                    raw: cand,
                });
            }
        }
        // OpenAI: choices
        else if (Array.isArray(obj.choices) && obj.choices.length > 0) {
            const ch = obj.choices[0];
            const msg = ch.message || ch.delta;
            if (msg) {
                let text = msg.content || '';
                let thinking = msg.reasoning_content || msg.reasoning || '';
                const toolCalls: any[] = [];

                if (Array.isArray(msg.tool_calls)) {
                    msg.tool_calls.forEach((tc: any) => {
                        toolCalls.push({
                            id: tc.id,
                            name: tc.function?.name,
                            args: tc.function?.arguments,
                        });
                    });
                }

                data.messages.push({
                    role: 'assistant',
                    roleLabel: 'Assistant Response',
                    text: text || undefined,
                    thinking: thinking || undefined,
                    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
                    raw: ch,
                });
            }
        }
        // 单纯简要提纯过的 Response: { content, thinking_signature, usage, ... }
        else if (obj.content && typeof obj.content === 'string') {
            data.messages.push({
                role: 'assistant',
                roleLabel: 'Assistant Response',
                text: obj.content,
                thinkingSignature: obj.thinking_signature || obj._session_thinking_id,
                raw: obj,
            });
        }
    }

    // 5. Usage 解析
    const usage = obj.usage || obj.usageMetadata;
    if (usage) {
        data.usage = {
            inputTokens: usage.prompt_tokens ?? usage.promptTokenCount ?? usage.input_tokens,
            outputTokens: usage.completion_tokens ?? usage.candidatesTokenCount ?? usage.output_tokens,
            cachedTokens: usage.prompt_tokens_details?.cached_tokens ?? usage.cachedContentTokenCount ?? usage.cached_tokens,
            totalTokens: usage.total_tokens ?? usage.totalTokenCount ?? usage.total_tokens,
        };
    }

    // 判断是否具备结构化要素
    if (
        data.systemPrompt ||
        data.messages.length > 0 ||
        data.tools.length > 0 ||
        data.config.model
    ) {
        data.isStructured = true;
    }

    return data;
}

export interface StructuredPayloadViewProps {
    rawPayload?: string;
    isResponse?: boolean;
    onCopyText?: (text: string) => Promise<boolean | void> | void;
}

export const StructuredPayloadView: React.FC<StructuredPayloadViewProps> = ({
    rawPayload,
    isResponse = false,
    onCopyText,
}) => {
    const { t } = useTranslation();
    const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

    // 折叠状态控制
    const [systemExpanded, setSystemExpanded] = useState(true);
    const [toolsExpanded, setToolsExpanded] = useState(false);
    const [configExpanded, setConfigExpanded] = useState(true);
    const [collapsedMessages, setCollapsedMessages] = useState<Record<number, boolean>>({});

    const [filterQuery, setFilterQuery] = useState('');

    const parsed = useMemo(() => {
        if (!rawPayload) return null;
        return parsePayloadToStructured(rawPayload, isResponse);
    }, [rawPayload, isResponse]);

    const handleCopy = async (text: string, id: string) => {
        if (onCopyText) {
            await onCopyText(text);
        } else {
            await copyToClipboard(text);
        }
        setCopiedIndex(id);
        setTimeout(() => setCopiedIndex(null), 1800);
    };

    const toggleMessageCollapse = (idx: number) => {
        setCollapsedMessages(prev => ({ ...prev, [idx]: !prev[idx] }));
    };

    if (!parsed || !parsed.isStructured) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center text-gray-400 select-none">
                <Brain size={32} className="mb-2 opacity-30 text-gray-400" />
                <span className="text-xs">{t('monitor.details.structured_not_detected', '未检测到结构化大模型指令（点击右上角查看完整代码）')}</span>
            </div>
        );
    }

    // 过滤消息
    const filteredMessages = parsed.messages.filter((msg) => {
        if (!filterQuery.trim()) return true;
        const q = filterQuery.toLowerCase();
        return (
            msg.text?.toLowerCase().includes(q) ||
            msg.thinking?.toLowerCase().includes(q) ||
            msg.roleLabel.toLowerCase().includes(q) ||
            msg.toolCalls?.some(tc => tc.name.toLowerCase().includes(q))
        );
    });

    return (
        <div className="h-full flex flex-col min-h-0 bg-gray-50/50 dark:bg-base-100 font-sans">
            {/* 顶栏快速搜索 */}
            <div className="px-4 py-2 bg-white dark:bg-base-200 border-b border-gray-200 dark:border-base-300 flex items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-2 flex-1 max-w-sm relative">
                    <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        value={filterQuery}
                        onChange={(e) => setFilterQuery(e.target.value)}
                        placeholder={t('monitor.details.search_structured_placeholder', '在对话、系统词与工具中搜索...')}
                        className="input input-xs pl-7 pr-2 w-full bg-gray-50 dark:bg-base-100 border-gray-200 dark:border-base-300 text-xs rounded-lg focus:border-blue-500 focus:outline-hidden"
                    />
                </div>

                <div className="flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400 shrink-0">
                    {parsed.config.model && (
                        <span className="px-2 py-0.5 rounded-md font-mono bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800/50 font-bold">
                            {parsed.config.model}
                        </span>
                    )}
                    {parsed.tools.length > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-base-300 text-gray-700 dark:text-gray-300 font-mono">
                            🛠️ {t('monitor.details.tools_count', { count: parsed.tools.length, defaultValue: `${parsed.tools.length} 个工具` })}
                        </span>
                    )}
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-base-300 text-gray-700 dark:text-gray-300 font-mono">
                        💬 {t('monitor.details.messages_count', { count: parsed.messages.length, defaultValue: `${parsed.messages.length} 轮消息` })}
                    </span>
                </div>
            </div>

            {/* 结构化滚动区域 */}
            <div className="flex-1 min-h-0 overflow-y-auto p-3.5 space-y-3">
                {/* 1. 模型与环境配置卡片 (Config) */}
                {(parsed.config.model || parsed.config.thinkingBudget || parsed.config.sessionId) && (
                    <div className="rounded-xl border border-gray-200/90 dark:border-base-300 bg-white dark:bg-base-200 shadow-2xs overflow-hidden text-xs">
                        <div
                            onClick={() => setConfigExpanded(!configExpanded)}
                            className="px-3 py-2 bg-gray-50/80 dark:bg-base-300/40 border-b border-gray-200 dark:border-base-300 flex items-center justify-between cursor-pointer select-none hover:bg-gray-100/60 transition-colors"
                        >
                            <div className="flex items-center gap-2 font-bold text-gray-800 dark:text-gray-200">
                                <Cpu size={13} className="text-blue-500" />
                                <span>{t('monitor.details.model_config_title', '模型环境与生成配置 (Model & Config)')}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-gray-400">
                                {configExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                            </div>
                        </div>

                        {configExpanded && (
                            <div className="p-3 grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px]">
                                {parsed.config.model && (
                                    <div className="p-2 rounded-lg bg-gray-50 dark:bg-base-100 border border-gray-200/70 dark:border-base-300">
                                        <span className="text-[10px] text-gray-400 block font-sans">{t('monitor.details.model_name', '模型名称 (Model)')}</span>
                                        <span className="font-bold text-blue-600 dark:text-blue-400 truncate block">
                                            {parsed.config.model}
                                        </span>
                                    </div>
                                )}
                                {parsed.config.thinkingBudget !== undefined && (
                                    <div className="p-2 rounded-lg bg-gray-50 dark:bg-base-100 border border-gray-200/70 dark:border-base-300">
                                        <span className="text-[10px] text-gray-400 block font-sans">{t('monitor.details.thinking_budget', '思考预算 (Thinking Budget)')}</span>
                                        <span className="font-bold text-amber-600 dark:text-amber-400">
                                            {parsed.config.thinkingBudget} Tokens
                                        </span>
                                    </div>
                                )}
                                {parsed.config.maxTokens !== undefined && (
                                    <div className="p-2 rounded-lg bg-gray-50 dark:bg-base-100 border border-gray-200/70 dark:border-base-300">
                                        <span className="text-[10px] text-gray-400 block font-sans">{t('monitor.details.max_tokens', '最大输出 (Max Tokens)')}</span>
                                        <span className="font-bold text-gray-700 dark:text-gray-300">
                                            {parsed.config.maxTokens}
                                        </span>
                                    </div>
                                )}
                                {parsed.config.sessionId && (
                                    <div className="p-2 rounded-lg bg-gray-50 dark:bg-base-100 border border-gray-200/70 dark:border-base-300">
                                        <span className="text-[10px] text-gray-400 block font-sans">Session ID</span>
                                        <span className="font-medium text-gray-600 dark:text-gray-400 truncate block" title={parsed.config.sessionId}>
                                            {parsed.config.sessionId}
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* 2. 系统提示词卡片 (System Prompt) */}
                {parsed.systemPrompt && (
                    <div className="rounded-xl border border-purple-200/90 dark:border-purple-900/50 bg-white dark:bg-base-200 shadow-2xs overflow-hidden text-xs">
                        <div
                            onClick={() => setSystemExpanded(!systemExpanded)}
                            className="px-3 py-2 bg-purple-50/70 dark:bg-purple-950/30 border-b border-purple-100 dark:border-purple-900/40 flex items-center justify-between cursor-pointer select-none hover:bg-purple-100/50 transition-colors"
                        >
                            <div className="flex items-center gap-2 font-bold text-purple-900 dark:text-purple-200">
                                <Brain size={13} className="text-purple-600 dark:text-purple-400" />
                                <span>{t('monitor.details.system_instruction_title', '系统提示词 (System Instruction)')}</span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-800 dark:text-purple-300 font-mono">
                                    {t('monitor.details.chars_count', { count: parsed.systemPrompt.length, defaultValue: `${parsed.systemPrompt.length} 字符` })}
                                </span>
                            </div>

                            <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                                <button
                                    type="button"
                                    onClick={() => handleCopy(parsed.systemPrompt!, 'sys')}
                                    className="btn btn-ghost btn-xs h-6 px-2 text-purple-800 dark:text-purple-300 hover:bg-purple-200/50 text-[10px] gap-1"
                                    title={t('monitor.details.copy_system_prompt', '复制系统提示词')}
                                >
                                    {copiedIndex === 'sys' ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                                    <span>{copiedIndex === 'sys' ? t('common.copied', '已复制') : t('common.copy', '复制')}</span>
                                </button>
                                <div className="text-purple-400">
                                    {systemExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                </div>
                            </div>
                        </div>

                        {systemExpanded && (
                            <div className="p-3 bg-purple-50/20 dark:bg-purple-950/10 font-mono text-xs whitespace-pre-wrap leading-relaxed select-text text-gray-800 dark:text-gray-200 max-h-80 overflow-y-auto">
                                {parsed.systemPrompt}
                            </div>
                        )}
                    </div>
                )}

                {/* 3. 工具配置卡片 (Tools Declarations) */}
                {parsed.tools.length > 0 && (
                    <div className="rounded-xl border border-amber-200/90 dark:border-amber-900/50 bg-white dark:bg-base-200 shadow-2xs overflow-hidden text-xs">
                        <div
                            onClick={() => setToolsExpanded(!toolsExpanded)}
                            className="px-3 py-2 bg-amber-50/70 dark:bg-amber-950/30 border-b border-amber-100 dark:border-amber-900/40 flex items-center justify-between cursor-pointer select-none hover:bg-amber-100/50 transition-colors"
                        >
                            <div className="flex items-center gap-2 font-bold text-amber-900 dark:text-amber-200">
                                <Wrench size={13} className="text-amber-600 dark:text-amber-400" />
                                <span>{t('monitor.details.tool_declarations_title', '工具函数声明 (Tool Declarations)')}</span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-mono">
                                    {t('monitor.details.available_functions_count', { count: parsed.tools.length, defaultValue: `${parsed.tools.length} 个可用函数` })}
                                </span>
                            </div>

                            <div className="flex items-center gap-1.5 text-amber-400">
                                {toolsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                            </div>
                        </div>

                        {toolsExpanded && (
                            <div className="p-3 grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-80 overflow-y-auto">
                                {parsed.tools.map((tool, idx) => (
                                    <div
                                        key={idx}
                                        className="p-2.5 rounded-lg border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/30 dark:bg-amber-950/20 space-y-1 font-mono text-[11px]"
                                    >
                                        <div className="flex items-center justify-between font-bold text-amber-900 dark:text-amber-200">
                                            <span>⚡ {tool.name}()</span>
                                            <button
                                                type="button"
                                                onClick={() => handleCopy(JSON.stringify(tool, null, 2), `tool-${idx}`)}
                                                className="btn btn-ghost btn-xs h-5 px-1.5 text-gray-500 hover:text-gray-900 dark:hover:text-white"
                                            >
                                                {copiedIndex === `tool-${idx}` ? <Check size={10} className="text-emerald-500" /> : <Copy size={10} />}
                                            </button>
                                        </div>
                                        {tool.description && (
                                            <p className="font-sans text-[11px] text-gray-600 dark:text-gray-400 line-clamp-2" title={tool.description}>
                                                {tool.description}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* 4. 对话消息流 (Messages / Contents) */}
                {filteredMessages.length > 0 && (
                    <div className="space-y-2.5 pt-1">
                        <div className="flex items-center justify-between px-1 text-xs font-bold text-gray-700 dark:text-gray-300">
                            <div className="flex items-center gap-1.5">
                                <MessageSquare size={13} className="text-blue-500" />
                                <span>{t('monitor.details.conversation_messages_title', '对话历史与消息轮次 (Conversation Messages)')}</span>
                            </div>
                            <span className="text-[10px] text-gray-400 font-normal">
                                {t('monitor.details.total_messages_count', { count: filteredMessages.length, defaultValue: `共 ${filteredMessages.length} 轮消息` })}
                            </span>
                        </div>

                        {filteredMessages.map((msg, idx) => {
                            const isCollapsed = collapsedMessages[idx] ?? false;
                            const isUser = msg.role === 'user';
                            const isAssistant = msg.role === 'assistant';
                            const isTool = msg.role === 'tool';

                            return (
                                <div
                                    key={idx}
                                    className={`rounded-xl border shadow-2xs transition-all overflow-hidden text-xs ${
                                        isUser
                                            ? 'border-blue-200 dark:border-blue-900/50 bg-white dark:bg-base-200'
                                            : isAssistant
                                            ? 'border-emerald-200 dark:border-emerald-900/50 bg-white dark:bg-base-200'
                                            : isTool
                                            ? 'border-amber-200 dark:border-amber-900/50 bg-white dark:bg-base-200'
                                            : 'border-gray-200 dark:border-base-300 bg-white dark:bg-base-200'
                                    }`}
                                >
                                    {/* 消息角色标题栏 */}
                                    <div
                                        onClick={() => toggleMessageCollapse(idx)}
                                        className={`px-3 py-1.5 border-b flex items-center justify-between cursor-pointer select-none transition-colors ${
                                            isUser
                                                ? 'bg-blue-50/70 dark:bg-blue-950/30 border-blue-100 dark:border-blue-900/40 text-blue-900 dark:text-blue-200'
                                                : isAssistant
                                                ? 'bg-emerald-50/70 dark:bg-emerald-950/30 border-emerald-100 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-200'
                                                : isTool
                                                ? 'bg-amber-50/70 dark:bg-amber-950/30 border-amber-100 dark:border-amber-900/40 text-amber-900 dark:text-amber-200'
                                                : 'bg-gray-50/70 dark:bg-base-300/40 border-gray-200 dark:border-base-300 text-gray-800 dark:text-gray-200'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2 font-bold">
                                            {isUser && <User size={13} className="text-blue-600 dark:text-blue-400" />}
                                            {isAssistant && <Bot size={13} className="text-emerald-600 dark:text-emerald-400" />}
                                            {isTool && <Terminal size={13} className="text-amber-600 dark:text-amber-400" />}
                                            <span>{msg.roleLabel}</span>
                                            <span className="text-[10px] opacity-60 font-mono font-normal">#{idx + 1}</span>
                                        </div>

                                        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                                            <button
                                                type="button"
                                                onClick={() => handleCopy(msg.text || JSON.stringify(msg.raw, null, 2), `msg-${idx}`)}
                                                className="btn btn-ghost btn-xs h-6 px-2 text-[10px] gap-1 opacity-80 hover:opacity-100"
                                                title={t('monitor.details.copy_turn_message', '复制本轮消息')}
                                            >
                                                {copiedIndex === `msg-${idx}` ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                                                <span>{copiedIndex === `msg-${idx}` ? t('common.copied', '已复制') : t('common.copy', '复制')}</span>
                                            </button>
                                            <div className="opacity-60">
                                                {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                                            </div>
                                        </div>
                                    </div>

                                    {/* 消息正文与内容 */}
                                    {!isCollapsed && (
                                        <div className="p-3 space-y-2.5">
                                            {/* 思维链展示 (Thinking Block) */}
                                            {msg.thinking && (
                                                <div className="p-2.5 rounded-lg bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 font-mono text-[11px] space-y-1">
                                                    <div className="flex items-center gap-1 font-bold text-amber-800 dark:text-amber-300">
                                                        <Sparkles size={11} />
                                                        <span>{t('monitor.details.thinking_process_title', '思考推理过程 (Thinking Process)')}</span>
                                                    </div>
                                                    <p className="whitespace-pre-wrap leading-relaxed text-gray-700 dark:text-gray-300">
                                                        {msg.thinking}
                                                    </p>
                                                </div>
                                            )}

                                            {/* 纯文本内容 */}
                                            {msg.text && (
                                                <div className="font-mono text-xs whitespace-pre-wrap leading-relaxed text-gray-800 dark:text-gray-200 select-text">
                                                    {msg.text}
                                                </div>
                                            )}

                                            {/* 工具调用块 (Tool Calls) */}
                                            {msg.toolCalls && msg.toolCalls.length > 0 && (
                                                <div className="space-y-1.5 pt-1">
                                                    {msg.toolCalls.map((tc, tcIdx) => (
                                                        <div
                                                            key={tcIdx}
                                                            className="p-2 rounded-lg bg-blue-50/40 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-800/40 font-mono text-[11px] space-y-1"
                                                        >
                                                            <div className="flex items-center justify-between font-bold text-blue-900 dark:text-blue-300">
                                                                <span>⚡ {t('monitor.details.call_tool_label', '调用工具')}: {tc.name}()</span>
                                                                {tc.id && <span className="text-[10px] opacity-60">ID: {tc.id}</span>}
                                                            </div>
                                                            {tc.args && (
                                                                <pre className="p-1.5 rounded bg-white dark:bg-base-100 overflow-x-auto text-[10px] text-gray-700 dark:text-gray-300">
                                                                    {typeof tc.args === 'string' ? tc.args : JSON.stringify(tc.args, null, 2)}
                                                                </pre>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* 工具返回结果 (Tool Result) */}
                                            {msg.toolResult && (
                                                <div className="p-2 rounded-lg bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 font-mono text-[11px] space-y-1">
                                                    <div className="flex items-center justify-between font-bold text-amber-900 dark:text-amber-300">
                                                        <span>📥 {t('monitor.details.tool_result_label', '工具执行结果')} {msg.toolResult.name ? `(${msg.toolResult.name})` : ''}</span>
                                                        {msg.toolResult.callId && <span className="text-[10px] opacity-60">Call ID: {msg.toolResult.callId}</span>}
                                                    </div>
                                                    <pre className="p-1.5 rounded bg-white dark:bg-base-100 overflow-x-auto text-[10px] text-gray-700 dark:text-gray-300">
                                                        {typeof msg.toolResult.result === 'string'
                                                            ? msg.toolResult.result
                                                            : JSON.stringify(msg.toolResult.result, null, 2)}
                                                    </pre>
                                                </div>
                                            )}

                                            {/* 思考签名 */}
                                            {msg.thinkingSignature && (
                                                <div className="text-[10px] font-mono text-gray-400 dark:text-gray-500 truncate" title={msg.thinkingSignature}>
                                                    {t('monitor.details.thinking_signature_label', '思考签名')}: {msg.thinkingSignature}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};
