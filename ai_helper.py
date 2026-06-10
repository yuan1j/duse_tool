import re
import json
import logging
from datetime import datetime, timedelta
from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL,
    DASHSCOPE_FAST_MODEL,
    DASHSCOPE_TIMEOUT,
    DASHSCOPE_TEMPERATURE,
    DASHSCOPE_TOP_P,
    ENABLE_DASHSCOPE,
)

logger = logging.getLogger(__name__)


class DashscopeClient:
    """Dashscope (通义千问) 客户端 - 所有 AI 功能统一入口"""

    def __init__(self):
        self.api_key = DASHSCOPE_API_KEY
        self.model = DASHSCOPE_MODEL
        self.fast_model = DASHSCOPE_FAST_MODEL
        self.timeout = DASHSCOPE_TIMEOUT
        self.temperature = DASHSCOPE_TEMPERATURE
        self.top_p = DASHSCOPE_TOP_P
        self.enabled = ENABLE_DASHSCOPE and bool(self.api_key)
        self._dashscope = None
        self._init_client()

    def _init_client(self):
        if not self.enabled:
            raise RuntimeError(
                "⚠️  DASHSCOPE_API_KEY 未配置！\n"
                "   请在 .env 文件中设置 DASHSCOPE_API_KEY=sk-你的key\n"
                "   获取地址: https://dashscope.console.aliyun.com/apiKey"
            )
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self._dashscope = dashscope
        except ImportError:
            raise RuntimeError(
                "⚠️  dashscope 库未安装！\n"
                "   请执行: pip install dashscope>=1.14.0"
            )

    def call(self, prompt, system_prompt=None, use_fast=True, max_tokens=512):
        """调用大模型 - 所有 AI 功能统一走此方法"""
        if not self.enabled or self._dashscope is None:
            raise RuntimeError("Dashscope 客户端未正确初始化")

        model = self.fast_model if use_fast else self.model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            Generation = self._dashscope.Generation
            response = Generation.call(
                model=model,
                messages=messages,
                result_format='message',
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )

            if response.status_code == 200 and response.output:
                choices = response.output.get("choices", [])
                if choices and len(choices) > 0:
                    content = choices[0]["message"]["content"].strip()
                    if content:
                        return content

            logger.error("Dashscope 返回异常: status=%s, output=%s",
                         getattr(response, 'status_code', 'N/A'),
                         getattr(response, 'output', 'N/A'))
            raise RuntimeError(f"AI 服务返回异常: status_code={response.status_code}")

        except Exception as e:
            msg = str(e)
            logger.error("Dashscope 调用失败: %s", msg)
            raise RuntimeError(f"AI 服务调用失败: {msg}")

    def chat(self, messages, use_fast=True, max_tokens=1024):
        """带历史的对话调用 - messages 为列表，每项 {'role': 'user'|'assistant', 'content': str}

        system_prompt 若存在应放入 messages 首条 (role='system')。"""
        if not self.enabled or self._dashscope is None:
            raise RuntimeError("Dashscope 客户端未正确初始化")

        model = self.fast_model if use_fast else self.model
        if not messages:
            raise RuntimeError("对话消息不能为空")

        try:
            Generation = self._dashscope.Generation
            response = Generation.call(
                model=model,
                messages=list(messages),
                result_format='message',
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            if response.status_code == 200 and response.output:
                choices = response.output.get("choices", [])
                if choices and len(choices) > 0:
                    content = choices[0]["message"]["content"].strip()
                    if content:
                        return content
            logger.error("Dashscope 对话返回异常: status=%s", getattr(response, 'status_code', 'N/A'))
            raise RuntimeError(f"AI 对话服务返回异常")
        except Exception as e:
            logger.error("Dashscope 对话调用失败: %s", str(e))
            raise RuntimeError(f"AI 对话服务调用失败: {e}")


class AIHelper:
    """AI 辅助模块 - 所有功能必须使用 Dashscope 大模型"""

    def __init__(self):
        self._client = None
        self.keyword_patterns = self._build_keyword_patterns()

    @property
    def client(self):
        """延迟初始化 LLM 客户端，避免模块导入时立即连接"""
        if self._client is None:
            self._client = DashscopeClient()
        return self._client

    # ============================================================
    #  字段语义识别 - 用关键字辅助 LLM prompt，不做本地生成
    # ============================================================

    def _build_keyword_patterns(self):
        return {
            "姓名": ["name", "姓名", "名字", "申请人", "联系人", "负责人", "填报人", "员工"],
            "部门": ["department", "dept", "部门", "科室", "组别", "所属部门"],
            "职位": ["position", "title", "职位", "职务", "岗位"],
            "邮箱": ["email", "邮箱", "mail", "e-mail", "邮件"],
            "电话": ["tel", "phone", "电话", "手机", "mobile", "contact"],
            "日期": ["date", "日期", "时间", "day"],
            "地址": ["address", "地址", "location", "place", "地点"],
            "项目": ["project", "项目", "课题", "task", "任务"],
            "金额": ["amount", "price", "金额", "费用", "预算", "money", "cost"],
            "数量": ["quantity", "count", "num", "数量", "个数", "数目"],
            "原因": ["reason", "原因", "理由", "purpose", "目的"],
            "说明": ["remark", "note", "说明", "描述", "description", "detail", "详情"],
            "状态": ["status", "state", "状态", "情况"],
            "编号": ["id", "no", "number", "code", "编号", "单号"],
            "公司": ["company", "公司", "单位", "organization", "机构"],
            "标题": ["title", "subject", "标题", "主题", "topic"],
            "评分": ["score", "rating", "评分", "分数", "mark", "grade"],
            "百分比": ["percent", "percentage", "比例", "百分比", "rate"],
            "开始": ["start", "开始", "起始", "begin"],
            "结束": ["end", "结束", "截止", "finish", "stop"],
            "意见": ["opinion", "suggestion", "意见", "建议", "comment", "评价"],
        }

    def _detect_field_category(self, field):
        """识别字段语义类别 - 用于优化 prompt"""
        field_label = str(field.get("field_label", "") or "").lower()
        field_name = str(field.get("field_name", "") or "").lower()
        field_desc = str(field.get("field_description", "") or "").lower()

        combined_text = f"{field_label} {field_name} {field_desc}"

        for category, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    return category
        return "通用"

    # ============================================================
    #  核心公开方法 1: 字段智能推荐
    # ============================================================

    def recommend_field_value(self, field, existing_values=None):
        """
        单个字段智能推荐值 - 必须调用 LLM
        """
        field_type = field.get("field_type", "text")
        field_label = field.get("field_label", "字段")
        field_desc = field.get("field_description", "")
        options = field.get("field_options")
        category = self._detect_field_category(field)

        today = datetime.now().strftime("%Y-%m-%d")

        system_prompt = (
            "你是一个专业的中文表单填报助手。根据字段信息生成恰当、合理的示例填报内容。\n"
            "要求: 1. 只返回生成的值，不要任何解释、说明、引号、括号、前缀、后缀。\n"
            "2. 值必须符合字段类型，内容要真实、自然、符合中国国情。\n"
            "3. 日期格式必须是 YYYY-MM-DD。\n"
            "4. 数字只返回数字本身。\n"
            "5. 邮箱格式为 name@company.com。\n"
            "6. 手机号为 11 位，以 13/15/17/18/19 开头。\n"
            "7. 多行文本字段返回 30-80 字的通顺中文段落。\n"
            "8. 如果字段有选项，严格从选项中选一个返回。"
        )

        if options:
            opts_str = "、".join(options)
            prompt = (
                f"表单字段信息：\n"
                f"字段名称: {field_label}\n"
                f"字段描述: {field_desc}\n"
                f"字段类别: {category}\n"
                f"字段类型: {field_type}\n"
                f"可选值列表: {opts_str}\n\n"
                f"请严格从上述可选值中选择一个最合理的值。直接返回该值，不要加任何其他文字。"
            )
        else:
            type_hints = {
                "email": "标准企业邮箱格式，如 zhangsan@company.com",
                "tel": "11 位中国手机号，如 13800138000",
                "date": f"YYYY-MM-DD 格式的日期，参考今日: {today}",
                "number": "一个合理的正数（金额类字段返回带两位小数，数量类返回整数）",
                "textarea": "一段 30-80 字的通顺中文描述，内容要专业、具体",
                "text": "简短的中文内容，20 字以内",
                "select": "从给定选项中选择一个",
            }
            hint = type_hints.get(field_type, "简短中文内容")

            prompt = (
                f"表单字段信息：\n"
                f"字段名称: {field_label}\n"
                f"字段描述: {field_desc}\n"
                f"字段类别: {category}\n"
                f"字段类型: {field_type}\n"
                f"输出格式要求: {hint}\n"
                f"当前日期: {today}\n\n"
                f"请直接返回生成的填报值，不要加任何解释、引号、前缀、后缀。"
            )

        max_tokens = 200 if field_type == "textarea" else 100
        result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=max_tokens)
        return self._clean_output(result, field_type, options)

    # ============================================================
    #  核心公开方法 2: 字段内容优化
    # ============================================================

    def optimize_field(self, field, current_value=None):
        """
        字段内容优化/润色 - 必须调用 LLM
        """
        field_type = field.get("field_type", "text")
        field_label = field.get("field_label", "字段")
        field_desc = field.get("field_description", "")
        category = self._detect_field_category(field)
        options = field.get("field_options")

        if current_value is None or str(current_value).strip() == "":
            return self.recommend_field_value(field)

        stripped_value = str(current_value).strip()

        if field_type == "select" and options:
            system_prompt = (
                "你是一个表单助手。从给定选项列表中匹配最接近用户输入的值。"
                "只返回选项列表中的完整项，不要加任何其他文字。"
            )
            prompt = (
                f"字段: {field_label}\n"
                f"可选值: {'、'.join(options)}\n"
                f"用户输入: {stripped_value}\n\n"
                f"从可选值中选一个最接近用户输入的，直接返回该选项。"
            )
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=80)
            cleaned = self._clean_output(result, field_type, options)
            if cleaned in options:
                return cleaned
            lower_input = stripped_value.lower()
            for opt in options:
                if lower_input == str(opt).lower():
                    return opt
            for opt in options:
                if lower_input in str(opt).lower():
                    return opt
            return options[0]

        if field_type == "email":
            system_prompt = "你是格式校验助手。只返回标准格式的邮箱地址，其他文字一概不要。"
            prompt = (
                f"字段: {field_label}\n"
                f"当前值: {stripped_value}\n\n"
                f"若已是标准邮箱则原样返回；若缺少 @ 或域名则补全为企业邮箱格式。只返回最终邮箱地址。"
            )
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=80)
            return self._clean_output(result, field_type)

        if field_type == "tel":
            system_prompt = "你是格式校验助手。只返回 11 位中国手机号，其他文字一概不要。"
            prompt = (
                f"字段: {field_label}\n"
                f"当前值: {stripped_value}\n\n"
                f"若是有效的 11 位手机号则原样返回；否则生成一个合理的中国手机号。只返回 11 位数字。"
            )
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=60)
            return self._clean_output(result, field_type)

        if field_type == "date":
            today = datetime.now().strftime("%Y-%m-%d")
            system_prompt = "你是格式校验助手。只返回 YYYY-MM-DD 格式的日期，其他文字一概不要。"
            prompt = (
                f"字段: {field_label}\n"
                f"当前值: {stripped_value}\n"
                f"当前日期: {today}\n\n"
                f"解析用户输入，转换为 YYYY-MM-DD 格式。无效则返回一个合理的日期（如今天或近期日期）。只返回日期。"
            )
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=60)
            return self._clean_output(result, field_type)

        if field_type == "number":
            system_prompt = "你是数字校验助手。只返回一个数字，其他文字一概不要。"
            prompt = (
                f"字段: {field_label}\n"
                f"字段类别: {category}\n"
                f"当前值: {stripped_value}\n\n"
                f"若是有效数字则原样返回；无效则根据字段类别生成一个合理的数字。"
                f"金额类返回带两位小数的正数；数量类返回正整数。只返回数字本身。"
            )
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=80)
            return self._clean_output(result, field_type)

        if field_type in ("text", "textarea"):
            is_long = field_type == "textarea" or len(stripped_value) > 20
            system_prompt = (
                "你是一个专业的中文写作助手。对表单中的文字内容进行润色和优化。\n"
                "要求: 1. 保持原意，不要添加不相关的内容。\n"
                "2. 语言要专业、通顺、符合中文表达习惯。\n"
                "3. 只返回优化后的文字，不要加解释、引号、前缀、后缀。"
            )

            if is_long or field_type == "textarea":
                prompt = (
                    f"字段: {field_label}\n"
                    f"字段类别: {category}\n"
                    f"当前内容:\n{stripped_value}\n\n"
                    f"请对上述内容进行润色，使其更专业、完整、通顺。"
                    f"保持原意。返回优化后的文字，不要加任何其他内容。"
                )
                max_tokens = 512
            else:
                prompt = (
                    f"字段: {field_label}\n"
                    f"字段类别: {category}\n"
                    f"当前值: {stripped_value}\n\n"
                    f"该值过短或不够规范，请优化为更合适的填报内容。"
                    f"保持原意。返回优化后的文字，不要加任何其他内容。"
                )
                max_tokens = 200

            result = self.client.call(prompt, system_prompt, use_fast=False, max_tokens=max_tokens)
            return self._clean_output(result, field_type)

        result = self.client.call(
            f"字段: {field_label}，当前值: {stripped_value}。请优化此内容。只返回结果。",
            "你是表单助手。只返回结果，不加任何解释。",
            use_fast=True, max_tokens=120
        )
        return self._clean_output(result, field_type)

    # ============================================================
    #  核心公开方法 3: 批量一键填报（多个字段一次批量生成）
    # ============================================================

    def auto_fill_all(self, fields, existing_values=None):
        """
        批量一键填报 - 一次性生成所有字段值，减少 API 调用次数
        """
        existing_values = existing_values or {}
        fields_to_generate = []
        results = {}

        for f in fields:
            fname = f.get("field_name")
            if not fname:
                continue
            if existing_values.get(fname):
                results[fname] = existing_values[fname]
            else:
                fields_to_generate.append(f)

        if not fields_to_generate:
            return results

        if len(fields_to_generate) == 1:
            f = fields_to_generate[0]
            results[f["field_name"]] = self.recommend_field_value(f)
            return results

        today = datetime.now().strftime("%Y-%m-%d")

        field_info_lines = []
        for idx, f in enumerate(fields_to_generate, 1):
            label = f.get("field_label", f"字段{idx}")
            ftype = f.get("field_type", "text")
            cat = self._detect_field_category(f)
            info = f"{idx}. {label} (类型: {ftype}, 类别: {cat})"
            options = f.get("field_options")
            if options:
                info += f"，可选值: {'、'.join(options)}"
            field_info_lines.append(info)

        system_prompt = (
            "你是一个专业的中文表单填报助手。你需要为多个字段生成合理的填报值。\n"
            "严格按 JSON 格式返回: key 是序号(数字字符串)，value 是对应字段的值。\n"
            "值的要求: 日期 YYYY-MM-DD，邮箱 name@company.com，手机号 11 位数字，\n"
            "有选项的字段严格从选项中选一个。只返回 JSON 对象，不要任何其他文字。"
        )

        prompt = (
            f"请为以下表单字段生成合理的填报值。\n"
            f"当前日期: {today}\n\n"
            f"字段列表:\n" + "\n".join(field_info_lines) + "\n\n"
            f"请严格返回以下格式的 JSON:\n"
            f"{{\"1\": \"值1\", \"2\": \"值2\", ...}}\n\n"
            f"不要加任何前缀、后缀、解释、代码块标记，只返回纯 JSON。"
        )

        try:
            result = self.client.call(prompt, system_prompt, use_fast=True, max_tokens=800)
            parsed = self._parse_json_batch(result, fields_to_generate)

            for idx, f in enumerate(fields_to_generate, 1):
                key = f["field_name"]
                if key in parsed:
                    results[key] = parsed[key]
                else:
                    results[key] = self.recommend_field_value(f)

        except Exception as e:
            logger.warning("批量填报失败，降级为逐个调用: %s", str(e))
            for f in fields_to_generate:
                results[f["field_name"]] = self.recommend_field_value(f)

        return results

    # ============================================================
    #  辅助功能
    # ============================================================

    def get_suggestions(self, field, count=3):
        """获取多个候选值"""
        suggestions = []
        seen = set()
        for _ in range(count * 2):
            if len(suggestions) >= count:
                break
            try:
                val = self.recommend_field_value(field)
                if val and val not in seen:
                    seen.add(val)
                    suggestions.append(val)
            except Exception:
                break
        if not suggestions:
            return [self.recommend_field_value(field)]
        return suggestions

    def batch_recommend(self, fields):
        """批量推荐（详细版本）"""
        results = {}
        for field in fields:
            field_name = field.get("field_name")
            if field_name:
                try:
                    results[field_name] = {
                        "recommended_value": self.recommend_field_value(field),
                        "suggestions": self.get_suggestions(field, 2),
                        "field_category": self._detect_field_category(field),
                    }
                except Exception as e:
                    results[field_name] = {
                        "recommended_value": f"[AI 服务异常: {e}]",
                        "suggestions": [],
                        "field_category": self._detect_field_category(field),
                    }
        return results

    def is_using_llm(self):
        try:
            return self.client.enabled
        except Exception:
            return False

    # ============================================================
    #  多轮对话式一键填报（用户确认后才填报）
    # ============================================================

    def build_conversation_system_prompt(self, fields, form_name=None):
        field_lines = []
        for idx, f in enumerate(fields, 1):
            label = f.get("field_label", "")
            fname = f.get("field_name", "")
            ftype = f.get("field_type", "text")
            required = "必填" if f.get("is_required") else "选填"
            desc = f.get("field_description") or ""
            options = f.get("field_options")
            options_str = ""
            if options:
                options_str = f"，可选值：{'、'.join(options)}"
            field_lines.append(
                f"{idx}. 字段标签='{label}'（字段名={fname}，{required}，类型：{ftype}{options_str}）{(' - ' + desc) if desc else ''}"
            )
        form_info = f"【{form_name}】" if form_name else ""
        # 构建一个示例 JSON 模板，用前 3 个字段的 label 作为 key
        example_keys = [f'"{f.get("field_label", "")}"' for f in fields[:3]]
        json_template = "{" + ", ".join([f"{k}: \"<value>\"" for k in example_keys]) + "}"
        return (
            f"你是一个专业的表单填报助手。你将帮助用户通过多轮对话完成表单{form_info}的填写。\n\n"
            "============================================================\n"
            "表单字段（非常重要：下面列出的每个字段的「字段标签」必须作为 JSON 的 key，原样使用，不可更改大小写、不可增减空格、不可用其他名称替代）：\n"
            "============================================================\n"
            + "\n".join(field_lines) + "\n\n"
            "============================================================\n"
            "【必须遵守的回复格式】\n"
            "============================================================\n"
            "每次回复必须严格包含以下两部分，两部分之间用一个空行分隔：\n\n"
            "【第一部分】对用户说的自然语言（友好对话部分）。\n"
            "   - 可以是：询问某个字段的值、确认已收到的信息、或让用户确认结束。\n"
            "   - 这部分不要包含任何 JSON、字段列表、或 \"标签：值\" 格式的键值对。\n\n"
            "【第二部分】一个合法的 JSON 对象（必须放在回复的最后部分）：\n"
            "   - JSON 必须用 { 开头，用 } 结束。\n"
            "   - JSON 中的每个 key 必须严格等于上面列出的「字段标签」，不能改动任何字符。\n"
            "   - JSON 中的 value 是从用户本次对话中解析出来的字段值；如果本次没有解析到某个字段，就不要包含它。\n"
            "   - 字符串值必须用双引号括起来。\n"
            "   - 所有 key 必须用双引号括起来。\n"
            "   - 如果本次没有解析到任何字段值，则输出 {}。\n\n"
            f"正确的 JSON 示例（假设表单前几个字段用 field_label 作 key）：\n"
            f"  {json_template}\n\n"
            "其他规则：\n"
            "1. 如果用户一次性提供了多个字段，请全部解析并写入同一个 JSON 对象。\n"
            "2. 对下拉选择（select）类型字段，从可选值中挑选最接近的一个。\n"
            "3. 对日期类型字段，请解析为 YYYY-MM-DD 格式。\n"
            "4. 对数字类型字段，仅保留数字部分。\n"
            "5. 当所有必填字段都有值后，或用户明确说完成/确认，请在自然语言末尾或 JSON 之前输出特殊标记 <<DONE>>。\n"
            "============================================================\n"
        )

    def start_conversation_fill(self, fields, form_name=None, existing_values=None):
        """开启对话式填报会话，返回首个回复（ai_message, updated_values）"""
        values = dict(existing_values or {})
        system_prompt = self.build_conversation_system_prompt(fields, form_name)
        first_user_msg = "我想要通过对话填写这个表单，请开始询问我。"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": first_user_msg},
        ]
        return self._run_conversation_step(messages, fields, values,
                                           _return_messages=[{"role": "user", "content": first_user_msg}])

    def continue_conversation_fill(self, messages, fields, user_input, existing_values=None):
        """继续对话：传入历史 messages（不含 system 的用户/助手消息列表）与用户新输入，

        返回 (ai_message, updated_values, done_flag, new_messages)"""
        messages = list(messages) + [{"role": "user", "content": user_input}]
        system_prompt = self.build_conversation_system_prompt(fields)
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        return self._run_conversation_step(full_messages, fields, values=dict(existing_values or {}), _return_messages=messages)

    def _run_conversation_step(self, full_messages, fields, values, _return_messages=None):
        ai_text = self.client.chat(full_messages, use_fast=True, max_tokens=1500)
        done = "<<DONE>>" in ai_text
        ai_text_clean = ai_text.replace("<<DONE>>", "").strip()
        display_text_for_user = ai_text_clean
        parsed_json = {}

        # ==================== 调试日志 ====================
        print(f"\n[AI-conv] ---- Step start ----")
        print(f"[AI-conv] Input fields: {len(fields)}")
        for _f in fields:
            print(f"  field_name='{_f.get('field_name')}'  field_label='{_f.get('field_label')}'  type={_f.get('field_type')}")
        print(f"[AI-conv] AI text length: {len(ai_text_clean)}")
        print(f"[AI-conv] AI text (first 200): {ai_text_clean[:200]}")
        # ===================================================

        # --- 策略一：多种 JSON 提取策略，逐一尝试 ---
        json_strategies = [
            ("greedy  { ... }",         r'\{[\s\S]*\}'),           # 最外层大括号（贪心）
            ("non-greedy { ... }",      r'\{[\s\S]*?\}'),          # 第一个完整 {} 对
        ]
        json_candidate = None
        json_span = None
        for sname, spat in json_strategies:
            try:
                m = re.search(spat, ai_text_clean)
                if m:
                    cand = m.group(0).strip()
                    try:
                        data = json.loads(cand)
                        if isinstance(data, dict) and data:
                            json_candidate = data
                            json_span = (m.start(), m.end())
                            print(f"[AI-conv] JSON via '{sname}': {len(data)} keys")
                            print(f"[AI-conv] JSON keys: {list(data.keys())}")
                            break
                    except Exception:
                        continue
            except Exception:
                continue

        if json_candidate:
            parsed_json = json_candidate
            # 从对用户说的话中去掉 JSON 部分（保留前面的自然语言）
            before_json = ai_text_clean[:json_span[0]].strip()
            if before_json:
                display_text_for_user = before_json
            else:
                display_text_for_user = "已成功解析您提供的信息。"
        else:
            print("[AI-conv] No valid JSON found in AI reply. Trying fallback label:value parser.")

            # --- 策略二：后备解析，从 "标签：值" 列表行提取 ---
            fallback = {}
            field_label_to_field = {}
            for f in fields:
                lb = (f.get("field_label") or "").strip()
                fn = (f.get("field_name") or "").strip()
                if lb:
                    field_label_to_field[lb] = f
                if fn and fn != lb:
                    field_label_to_field[fn] = f

            for raw_line in ai_text_clean.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("{") or line.startswith("}"):
                    continue
                m = re.match(r'^([^：:]{1,50})\s*[：:]\s*(.+)$', line)
                if not m:
                    continue
                raw_key = m.group(1).strip()
                raw_val = m.group(2).strip()
                raw_key_clean = re.sub(r'^[\d\.\s\-\*\【\]]+', '', raw_key).strip()
                matched_field = None
                for lb_cand, f_obj in field_label_to_field.items():
                    if lb_cand and (raw_key_clean == lb_cand or raw_key_clean.startswith(lb_cand)):
                        matched_field = f_obj
                        break
                if matched_field is None:
                    for lb_cand, f_obj in field_label_to_field.items():
                        if lb_cand and (lb_cand in raw_key_clean or raw_key_clean in lb_cand):
                            matched_field = f_obj
                            break
                if matched_field is not None:
                    key_for_merge = matched_field.get("field_label") or matched_field.get("field_name")
                    fallback[key_for_merge] = raw_val.strip(" ,，;；\"'")

            if fallback:
                parsed_json = fallback
                print(f"[AI-conv] Fallback label:value parser found {len(fallback)} values")
                kept = []
                for l in ai_text_clean.splitlines():
                    if not re.match(r'^[^\n：:]{1,50}\s*[：:]\s*.+$', l.strip()):
                        kept.append(l)
                if kept:
                    display_text_for_user = "\n".join(kept).strip()
                else:
                    display_text_for_user = "已收到您提供的信息。"
            else:
                print("[AI-conv] Fallback parser also found nothing.")

        # --- 关键修复：字段 key 匹配（大小写不敏感 + 空白规范化）---
        def _norm(s):
            if not s:
                return ""
            s = str(s).strip().lower()
            s = re.sub(r'\s+', ' ', s)
            return s

        updated_values = dict(values) if values else {}
        # 建立规范化后的查找表（同时支持 field_name 和 field_label）
        norm_map = {}
        for f in fields:
            fl = _norm(f.get("field_label", ""))
            fn = _norm(f.get("field_name", ""))
            if fl:
                norm_map[fl] = f
            if fn and fn != fl:
                norm_map[fn] = f

        matched_count = 0
        unmatched_keys = []
        for key, raw_val in parsed_json.items():
            if raw_val is None or (isinstance(raw_val, str) and not str(raw_val).strip()):
                continue
            nkey = _norm(key)
            target_field = norm_map.get(nkey)
            if target_field is None:
                # 二次尝试：模糊子串匹配
                for nlabel, fld in norm_map.items():
                    if nlabel and nkey and (nlabel in nkey or nkey in nlabel):
                        target_field = fld
                        break
            if target_field is None:
                unmatched_keys.append(key)
                continue
            fn = target_field["field_name"]
            ftype = target_field.get("field_type", "text")
            opts = target_field.get("field_options")
            try:
                cleaned = self._clean_output(str(raw_val), ftype, opts)
            except Exception:
                cleaned = str(raw_val).strip()
            if cleaned:
                updated_values[fn] = cleaned
                matched_count += 1
                print(f"[AI-conv]  ✓ key='{key}' → field_name='{fn}' (label='{target_field.get('field_label')}') value='{cleaned}'")

        if unmatched_keys:
            print(f"[AI-conv]  ✗ Unmatched JSON keys: {unmatched_keys}")
        print(f"[AI-conv] Step result: matched={matched_count}/{len(parsed_json)} JSON keys, updated_values has {len(updated_values)} entries")
        print(f"[AI-conv] updated_values keys: {list(updated_values.keys())}")

        # --- 构造返回 messages ---
        new_messages = list(_return_messages) if _return_messages is not None else []
        display_text = display_text_for_user.strip()
        if not display_text:
            display_text = "已收到您的信息，请继续或确认结束。"
        new_messages.append({"role": "assistant", "content": display_text})

        print(f"[AI-conv] ---- Step end ----\n")
        return display_text, updated_values, done, new_messages

    def finalize_conversation_fill(self, fields, values):
        """用户确认后，将解析的值补齐为完整填报数据，缺省值或合理推荐补全（不强制）。

        返回最终的 submission_data（仅填充已解析的字段；未解析到的为空字符串）。"""
        submission_data = {}
        for f in fields:
            fn = f.get("field_name")
            if not fn:
                continue
            if fn in values and values[fn] not in ("", None):
                submission_data[fn] = values[fn]
            else:
                submission_data[fn] = ""
        return submission_data

    # ============================================================
    #  LLM 输出清理 - 确保返回干净、可用的值
    # ============================================================

    def _clean_output(self, text, field_type, options=None):
        """清理大模型输出，移除所有解释性文字、前缀、代码块等"""
        if not text:
            return ""

        text = str(text).strip()
        original = text

        text = re.sub(r'```(?:json|text|python)?\s*|\s*```', '', text, flags=re.IGNORECASE)
        text = text.strip()

        if text.startswith('{') and text.endswith('}'):
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    vals = [str(v) for v in data.values() if v is not None]
                    if vals:
                        text = vals[0]
            except Exception:
                pass

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            text = lines[0]

        text = text.strip('"').strip("'").strip()

        for _ in range(3):
            prev = text
            text = re.sub(r'^[\*\-•\s]+\s*', '', text)
            text = re.sub(r'^[\d一二三四五六七八九十]+[.、)\s]+\s*', '', text)
            text = re.sub(r'^[A-Za-z][.)\)]\s+', '', text)
            text = re.sub(
                r'^(?:(?:推荐|生成)?(?:值|结果|答案|姓名|内容|邮箱|电话|手机号|日期|部门|金额|职位|标题|简介|项目))\s*[:：]\s*',
                '', text, flags=re.IGNORECASE)
            text = re.sub(r'^(?:我(?:认为|推荐|建议)|应该是|正确的|最终的|优化后)?(?:的)?(?:答案|结果|内容)?\s*[:：]?\s*', '', text)
            text = text.strip().strip('"').strip("'").strip()
            if text == prev:
                break

        text = re.sub(r'["\'`]$', '', text).strip()

        if field_type == "number":
            m = re.search(r'-?\d+(?:\.\d+)?', text)
            if m:
                return m.group(0)
        elif field_type == "email":
            m = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
            if m:
                return m.group(0)
        elif field_type == "tel":
            digits = re.sub(r'\D', '', text)
            if len(digits) >= 7:
                return digits[:11]
        elif field_type == "date":
            m = re.search(r'\d{4}[-/年]\s*\d{1,2}[-/月]\s*\d{1,2}', text)
            if m:
                t = m.group(0)
                t = re.sub(r'[年月]', '-', t)
                t = t.replace('日', '').replace('/', '-')
                parts = [p.strip().zfill(2) for p in t.split('-')]
                if len(parts) == 3:
                    try:
                        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    except (ValueError, IndexError):
                        pass
            m = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text)
            if m:
                raw = m.group(0)
                parts = re.split(r'[-/]', raw)
                try:
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                except (ValueError, IndexError):
                    pass
        elif field_type == "datetime":
            m = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}', text)
            if m:
                return m.group(0)
        elif field_type == "select" and options:
            text_lower = text.strip().lower()
            text_nospace = re.sub(r'\s+', '', text_lower)
            best_match = None
            best_score = 0
            for opt in options:
                opt_lower = str(opt).lower()
                opt_nospace = re.sub(r'\s+', '', opt_lower)
                if opt_lower == text_lower:
                    return opt
                if opt_nospace == text_nospace:
                    return opt
                if opt_lower in text_lower or text_lower in opt_lower:
                    score = max(len(opt_lower), len(text_lower))
                    if score > best_score:
                        best_match = opt
                        best_score = score
                    continue
                common = sum(1 for c in text_lower if c in opt_lower)
                denom = max(len(opt_lower), len(text_lower))
                if common > 0 and denom > 0 and common / denom > 0.4:
                    if common > best_score:
                        best_match = opt
                        best_score = common
            if best_match:
                return best_match

        if not text:
            text = original.strip().split("\n")[0].strip() if original else ""

        return text.strip()

    def _parse_json_batch(self, text, fields):
        """解析批量 JSON 返回"""
        if not text:
            return {}

        text = text.strip()
        text = re.sub(r'```(?:json)?\s*|\s*```', '', text, flags=re.IGNORECASE)
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if not m:
                return {}
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                return {}

        if not isinstance(data, dict):
            return {}

        results = {}
        for idx, f in enumerate(fields, 1):
            fname = f.get("field_name")
            if not fname:
                continue
            ftype = f.get("field_type", "text")
            options = f.get("field_options")

            value = None
            if str(idx) in data:
                value = data[str(idx)]
            elif fname in data:
                value = data[fname]
            elif isinstance(data, dict):
                for k, v in data.items():
                    if str(idx) in str(k):
                        value = v
                        break

            if value is not None:
                cleaned = self._clean_output(str(value), ftype, options)
                if cleaned:
                    results[fname] = cleaned

        return results


ai_helper = AIHelper()
