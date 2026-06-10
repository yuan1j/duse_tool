import gradio as gr
from datetime import datetime
from config import APP_TITLE, APP_VERSION, FIELD_TYPES, FIELD_TYPES_CN, DEFAULT_AI_TIPS
from form_manager import form_manager
from ai_helper import ai_helper
from db import db


class DataEntryApp:
    def __init__(self):
        self.current_form_id = None

    _CUSTOM_CSS = """
        .gradio-container { font-size: 0.75em !important; }
        h1, h2, h3, h4 { font-size: 1.2em !important; }
        .md { font-size: 0.9em !important; }
        .label-wrap { font-size: 0.85em !important; }
        button { font-size: 0.9em !important; }
        .svelte-1gfkn6j { font-size: 0.85em !important; }
    """

    def build_interface(self):
        with gr.Blocks(title=APP_TITLE) as demo:
            gr.Markdown(f"## {APP_TITLE} v{APP_VERSION}  \n<small>基于 Gradio & SQLite3 · 支持表单自定义 / AI 智能辅助</small>")

            with gr.Tabs() as main_tabs:
                with gr.Tab("📝 数据填报"):
                    self._build_submission_tab()

                with gr.Tab("🛠️ 表单设计"):
                    self._build_form_design_tab()

                with gr.Tab("📋 表单管理"):
                    self._build_form_management_tab()

                with gr.Tab("📑 模板管理"):
                    self._build_template_tab()

                with gr.Tab("📊 数据查看"):
                    self._build_data_view_tab()

            gr.Markdown("---\n<small>AI辅助功能基于智能推荐规则，可帮助快速完成填报内容。</small>")

        return demo

    def _get_form_choices(self):
        forms = db.get_all_forms()
        return [(f"{f['name']} (ID: {f['id']})", f["id"]) for f in forms]

    def _build_submission_tab(self):
        form_id_state = gr.State(None)
        fields_state = gr.State([])

        conv_messages = gr.State([])
        conv_values = gr.State({})
        conv_form_id = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**选择表单**")
                submission_form_dd = gr.Dropdown(label="表单列表", choices=[], interactive=True)
                refresh_forms_btn = gr.Button("🔄 刷新表单列表", variant="secondary", size="sm")
                submission_info = gr.Markdown("👈 请先选择一个表单")

                gr.Markdown("**快捷操作**")
                with gr.Row():
                    auto_fill_btn = gr.Button("✨ AI 对话填报", variant="primary", size="sm")
                    clear_form_btn = gr.Button("🗑️ 清空", variant="stop", size="sm")

                conv_group = gr.Group(visible=False)
                with conv_group:
                    gr.Markdown("**🤖 AI 多轮对话**")
                    conv_chatbot = gr.Chatbot(height=280, show_label=False)
                    with gr.Row():
                        conv_input = gr.Textbox(
                            label="",
                            placeholder="告诉 AI 您的信息...",
                            scale=4,
                        )
                        conv_send = gr.Button("发送", variant="primary", size="sm", scale=1)
                    with gr.Row():
                        conv_preview_btn = gr.Button("📋 解析值", variant="secondary", size="sm")
                        conv_confirm_btn = gr.Button("✅ 填入表单", variant="primary", size="sm")
                        conv_stop_btn = gr.Button("❌ 结束", variant="stop", size="sm")
                    conv_preview_md = gr.Markdown("")

                gr.Markdown("**提交结果**")
                submission_result = gr.Markdown("")

            with gr.Column(scale=2):
                dynamic_components = gr.State([])
                form_area = gr.Markdown("👈 请先选择一个表单开始填报")

                @gr.render(inputs=[form_id_state])
                def render_dynamic_form(selected_form_id):
                    if not selected_form_id:
                        return [gr.Markdown("👈 请先选择一个表单开始填报")]

                    fields = db.get_fields_by_form(selected_form_id)
                    if not fields:
                        return [
                            gr.Markdown("⚠️ 该表单尚未定义任何字段"),
                            gr.Markdown("请先在【表单设计】标签页中为该表单添加字段")
                        ]

                    form_data = db.get_form(selected_form_id)
                    field_components = []

                    gr.Markdown(f"### 📄 {form_data['name']}")

                    for idx, field in enumerate(fields):
                        field_name = field["field_name"]
                        field_label = field["field_label"] + (" ⭐" if field["is_required"] else "")
                        field_type = field["field_type"]
                        field_desc = field.get("field_description") or DEFAULT_AI_TIPS.get(field_type, "")
                        default_val = field.get("default_value") or ""

                        with gr.Row():
                            if field_type == "text":
                                comp = gr.Textbox(label=field_label, placeholder=field_desc, value=default_val, scale=10)
                            elif field_type == "textarea":
                                comp = gr.Textbox(label=field_label, placeholder=field_desc, value=default_val, lines=3, scale=10)
                            elif field_type == "number":
                                try:
                                    val = float(default_val) if default_val else None
                                except (ValueError, TypeError):
                                    val = None
                                comp = gr.Number(label=field_label, placeholder=field_desc, value=val, scale=10)
                            elif field_type == "date":
                                comp = gr.Textbox(label=field_label, placeholder=field_desc + " (YYYY-MM-DD)", value=default_val, scale=10)
                            elif field_type == "email":
                                comp = gr.Textbox(label=field_label, placeholder=field_desc, value=default_val, scale=10)
                            elif field_type == "tel":
                                comp = gr.Textbox(label=field_label, placeholder=field_desc, value=default_val, scale=10)
                            elif field_type == "select":
                                options = field.get("field_options") or []
                                val = default_val if default_val in options else None
                                comp = gr.Dropdown(label=field_label, choices=options, value=val, allow_custom_value=True, scale=10)
                            else:
                                comp = gr.Textbox(label=field_label, placeholder=field_desc, value=default_val, scale=10)

                            opt_btn = gr.Button(
                                "🔮",
                                variant="secondary",
                                size="sm",
                                min_width=40,
                                scale=1
                            )

                        def create_optimize_handler(field_obj, current_idx=idx):
                            def handler(current_value):
                                try:
                                    if field_obj["field_type"] == "number":
                                        current_str = str(current_value) if current_value is not None else ""
                                        optimized = ai_helper.optimize_field(field_obj, current_str)
                                        try:
                                            return float(optimized)
                                        except (ValueError, TypeError):
                                            return optimized
                                    else:
                                        current_str = str(current_value) if current_value is not None else ""
                                        return ai_helper.optimize_field(field_obj, current_str)
                                except Exception as e:
                                    return current_value
                            return handler

                        handler = create_optimize_handler(field)
                        opt_btn.click(handler, inputs=[comp], outputs=[comp])
                        field_components.append((field, comp))

                    with gr.Row():
                        submit_btn = gr.Button("💾 提交填报", variant="primary", size="sm", scale=2)
                        quick_auto_fill = gr.Button("✨ 全部AI一键填报", variant="secondary", size="sm", scale=1)

                    result_output = gr.Markdown("")

                    input_components = [c for (_, c) in field_components]

                    # -------------- handlers --------------
                    def submit_handler(*args):
                        submission_data = {}
                        for i, (field_obj, _) in enumerate(field_components):
                            field_name = field_obj["field_name"]
                            val = args[i] if i < len(args) else ""
                            if val is None:
                                val = ""
                            submission_data[field_name] = val

                        try:
                            submission_id = form_manager.save_form_submission(selected_form_id, submission_data)
                            return f"✅ 填报成功！记录ID: {submission_id}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        except ValueError as e:
                            return f"❌ 验证失败：\n{str(e)}"
                        except Exception as e:
                            return f"❌ 提交失败: {str(e)}"

                    def auto_fill_handler():
                        filled = form_manager.auto_fill_form(selected_form_id)
                        results = []
                        for field_obj, _ in field_components:
                            val = filled.get(field_obj["field_name"], "")
                            if field_obj["field_type"] == "number":
                                try:
                                    results.append(float(val) if val else None)
                                except (ValueError, TypeError):
                                    results.append(None)
                            else:
                                results.append(val)
                        return results

                    def clear_handler():
                        results = []
                        for field_obj, _ in field_components:
                            if field_obj["field_type"] == "number":
                                results.append(None)
                            else:
                                results.append("")
                        return results

                    def build_form_results_from_values(values):
                        results = []
                        for field_obj, _ in field_components:
                            fn = field_obj["field_name"]
                            val = values.get(fn, "")
                            if field_obj["field_type"] == "number":
                                try:
                                    results.append(float(val) if val not in ("", None) else None)
                                except (ValueError, TypeError):
                                    results.append(None)
                            else:
                                results.append(val if val is not None else "")
                        return results

                    def _make_preview_md(values_dict, form_id):
                        """根据 values dict 和 form_id 生成预览 markdown"""
                        fields_local = db.get_fields_by_form(form_id)
                        if not fields_local:
                            return "（无可填字段）"
                        required_missing = []
                        lines = []
                        total_filled = 0
                        for f in fields_local:
                            fn = f["field_name"]
                            label = f["field_label"]
                            required = f["is_required"]
                            v = values_dict.get(fn, "")
                            tag = "⭐" if required else ""
                            if v in ("", None):
                                if required:
                                    required_missing.append(label)
                                lines.append(f"- {tag} **{label}**：_（空）_")
                            else:
                                total_filled += 1
                                lines.append(f"- {tag} **{label}**：`{v}`")
                        header = f"**📋 当前解析到的字段值（{total_filled}/{len(fields_local)}）**\n"
                        if required_missing:
                            header += f"> ⚠️ 必填项缺失：{', '.join(required_missing)}\n\n"
                        else:
                            header += "> ✅ 可点击【✅ 确认并填入表单】\n\n"
                        return header + "\n".join(lines)

                    def start_conv_fill():
                        try:
                            current_vals = {}
                            for field_obj, _ in field_components:
                                current_vals[field_obj["field_name"]] = ""
                            print(f"\n[APP] start_conv_fill: form_id={selected_form_id}, initial fields={len(current_vals)}")
                            res = form_manager.start_conversation_fill(
                                selected_form_id, existing_values=current_vals
                            )
                            print(f"[APP] start_conv_fill result: ai_message={len(res['ai_message'])} chars, values={len(res['values'])} entries")
                            preview_md = _make_preview_md(res["values"], selected_form_id)
                            return (
                                gr.update(visible=True),
                                [{"role": "assistant", "content": res["ai_message"]}],
                                "",
                                preview_md,
                                res["messages"],
                                res["values"],
                                selected_form_id,
                            )
                        except Exception as e:
                            print(f"[APP] start_conv_fill ERROR: {e}")
                            return (
                                gr.update(visible=True),
                                [{"role": "assistant", "content": f"❌ 开启对话失败: {e}"}],
                                "",
                                "",
                                [],
                                {},
                                selected_form_id,
                            )

                    def send_conv(user_msg, chat_history, messages, form_id_conv, values):
                        if not user_msg or not user_msg.strip():
                            return "", chat_history, messages, values, ""
                        try:
                            print(f"\n[APP] send_conv: form_id={form_id_conv}, user_msg='{user_msg[:100]}'")
                            print(f"[APP] send_conv: incoming values has {len(values)} entries: {list(values.keys())}")
                            res = form_manager.continue_conversation_fill(
                                form_id_conv, messages, user_msg.strip(), existing_values=values
                            )
                            print(f"[APP] send_conv: AI replied, parsed values has {len(res['values'])} entries")
                            print(f"[APP] send_conv: returned values keys: {list(res['values'].keys())}")
                            # 打印每个解析到的非空值
                            for k, vv in res["values"].items():
                                if vv and str(vv).strip():
                                    print(f"  - {k} = '{vv}'")
                            new_history = list(chat_history) + [
                                {"role": "user", "content": user_msg.strip()},
                                {"role": "assistant", "content": res["ai_message"]},
                            ]
                            # 自动生成更新后的预览
                            new_preview = _make_preview_md(res["values"], form_id_conv)
                            return "", new_history, res["messages"], res["values"], new_preview
                        except Exception as e:
                            print(f"[APP] send_conv ERROR: {e}")
                            new_history = list(chat_history) + [
                                {"role": "user", "content": user_msg.strip()},
                                {"role": "assistant", "content": f"❌ 对话失败: {e}"},
                            ]
                            # 出错时也更新预览，显示旧值
                            error_preview = (f"> ❌ 错误：{e}\n\n" +
                                             _make_preview_md(values, form_id_conv) if form_id_conv else f"> ❌ 错误：{e}")
                            return "", new_history, messages, values, error_preview

                    def preview_conv(values, form_id_conv):
                        return _make_preview_md(values, form_id_conv)

                    def confirm_and_fill(values):
                        results = build_form_results_from_values(values)
                        return (
                            gr.update(visible=False),
                            [],
                            "",
                            "",
                            [],
                            {},
                            None,
                            *results,
                        )

                    def stop_conv():
                        return (
                            gr.update(visible=False),
                            [],
                            "",
                            "",
                            [],
                            {},
                            None,
                        )

                    # -------------- 事件绑定 --------------
                    submit_btn.click(submit_handler, inputs=input_components, outputs=[result_output])
                    auto_fill_btn.click(
                        start_conv_fill,
                        outputs=[
                            conv_group,
                            conv_chatbot,
                            conv_input,
                            conv_preview_md,
                            conv_messages,
                            conv_values,
                            conv_form_id,
                        ],
                    )
                    quick_auto_fill.click(auto_fill_handler, outputs=input_components)
                    clear_form_btn.click(clear_handler, outputs=input_components)

                    conv_send.click(
                        send_conv,
                        inputs=[conv_input, conv_chatbot, conv_messages, conv_form_id, conv_values],
                        outputs=[conv_input, conv_chatbot, conv_messages, conv_values, conv_preview_md],
                    )
                    conv_input.submit(
                        send_conv,
                        inputs=[conv_input, conv_chatbot, conv_messages, conv_form_id, conv_values],
                        outputs=[conv_input, conv_chatbot, conv_messages, conv_values, conv_preview_md],
                    )
                    conv_preview_btn.click(
                        preview_conv,
                        inputs=[conv_values, conv_form_id],
                        outputs=[conv_preview_md],
                    )
                    conv_confirm_btn.click(
                        confirm_and_fill,
                        inputs=[conv_values],
                        outputs=[
                            conv_group,
                            conv_chatbot,
                            conv_input,
                            conv_preview_md,
                            conv_messages,
                            conv_values,
                            conv_form_id,
                            *input_components,
                        ],
                    )
                    conv_stop_btn.click(
                        stop_conv,
                        outputs=[
                            conv_group,
                            conv_chatbot,
                            conv_input,
                            conv_preview_md,
                            conv_messages,
                            conv_values,
                            conv_form_id,
                        ],
                    )

                    return [submit_btn, quick_auto_fill, result_output]

        refresh_forms_btn.click(
            lambda: gr.update(choices=self._get_form_choices(), value=None),
            outputs=[submission_form_dd]
        )

        def on_submission_form_change(form_id):
            if not form_id:
                return None, [], "👈 请先选择一个表单"
            form_data = form_manager.get_form_with_fields(form_id)
            if not form_data:
                return None, [], "❌ 表单不存在，请刷新列表"
            fields = form_data.get("fields", [])
            desc_line = f" · 描述：{(form_data.get('description') or '无')[:30]}" if form_data.get('description') else ""
            info = f"**{form_data['name']}** · {len(fields)}字段{desc_line}"
            if not fields:
                info += "\n⚠️ 该表单暂无字段，请先添加字段"
            return form_id, fields, info

        submission_form_dd.change(
            on_submission_form_change,
            inputs=[submission_form_dd],
            outputs=[form_id_state, fields_state, submission_info]
        )

    def _build_form_design_tab(self):
        design_form_id_state = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**表单基本信息**")
                design_form_name = gr.Textbox(label="表单名称 *", placeholder="例如：员工信息登记表")
                design_form_desc = gr.Textbox(label="表单描述", placeholder="简要描述表单用途（可选）", lines=2)

                with gr.Row():
                    create_form_btn = gr.Button("➕ 创建新表单", variant="primary", size="sm")
                    update_form_btn = gr.Button("💾 更新表单", variant="secondary", size="sm")

                design_form_dd = gr.Dropdown(label="选择已有表单进行编辑", choices=[])
                refresh_design_btn = gr.Button("🔄 刷新列表", variant="secondary", size="sm")

                design_message = gr.Markdown("")

                gr.Markdown("**添加字段**")
                field_label = gr.Textbox(label="字段标签 *", placeholder="例如：姓名、手机号、邮箱")
                field_type = gr.Dropdown(
                    label="字段类型 *",
                    choices=[(FIELD_TYPES_CN[ft], ft) for ft in FIELD_TYPES],
                    value="text"
                )
                field_required = gr.Checkbox(label="设为必填项", value=False)
                field_desc = gr.Textbox(label="字段描述/提示", placeholder="填写提示或说明（可选）")
                field_default = gr.Textbox(label="默认值", placeholder="默认填充值（可选）")
                field_options = gr.Textbox(
                    label="下拉选项（下拉类型时用，逗号分隔）",
                    placeholder="选项1,选项2,选项3"
                )

                with gr.Row():
                    add_field_btn = gr.Button("➕ 添加字段", variant="primary", size="sm")
                    clear_field_btn = gr.Button("🔄 清空字段表单", variant="secondary", size="sm")

            with gr.Column(scale=2):
                gr.Markdown("**已添加的字段**")
                field_list_output = gr.Markdown("尚未添加任何字段，请先创建或选择表单")

        def _get_field_list_md(form_id):
            if not form_id:
                return "尚未添加任何字段"
            fields = db.get_fields_by_form(form_id)
            if not fields:
                return "**该表单暂无字段**"
            md = "| 序号 | 字段标签 | 类型 | 必填 | 描述 |\n|---|---|---|---|---|\n"
            for i, f in enumerate(fields, 1):
                required = "✅" if f["is_required"] else "—"
                type_cn = FIELD_TYPES_CN.get(f["field_type"], f["field_type"])
                desc = (f.get("field_description") or "—")[:40]
                md += f"| {i} | {f['field_label']} | {type_cn} | {required} | {desc} |\n"
            return md

        def on_create_form(name, desc, current_form_id):
            try:
                new_id = form_manager.create_new_form(name, desc)
                choices = self._get_form_choices()
                msg = f"✅ 表单创建成功！ID: {new_id}"
                return new_id, gr.update(choices=choices, value=new_id), msg, _get_field_list_md(new_id)
            except ValueError as e:
                return current_form_id, gr.update(), f"❌ {str(e)}", _get_field_list_md(current_form_id)

        def on_update_form(form_id, name, desc):
            if not form_id:
                return gr.update(), "❌ 请先选择或创建一个表单"
            try:
                form_manager.db.update_form(form_id, name, desc)
                choices = self._get_form_choices()
                return gr.update(choices=choices, value=form_id), "✅ 表单信息已更新"
            except Exception as e:
                return gr.update(), f"❌ 更新失败: {str(e)}"

        def on_design_form_selected(form_id):
            if not form_id:
                return None, "", "", "", "尚未添加任何字段"
            form = db.get_form(form_id)
            if not form:
                return None, "", "", "❌ 表单不存在", "尚未添加任何字段"
            return form_id, form.get("name", ""), form.get("description", "") or "", "", _get_field_list_md(form_id)

        def on_add_field(form_id, label, ftype, required, desc, default, options):
            if not form_id:
                return _get_field_list_md(form_id), "❌ 请先创建或选择一个表单", label, desc, default, options
            if not label or not label.strip():
                return _get_field_list_md(form_id), "❌ 字段标签不能为空", label, desc, default, options
            try:
                option_list = None
                if options and options.strip():
                    option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
                form_manager.add_form_field(
                    form_id=form_id,
                    field_label=label,
                    field_type=ftype,
                    is_required=required,
                    field_description=desc,
                    default_value=default,
                    field_options=option_list
                )
                return _get_field_list_md(form_id), f"✅ 字段【{label}】添加成功", "", "", "", ""
            except ValueError as e:
                return _get_field_list_md(form_id), f"❌ {str(e)}", label, desc, default, options

        create_form_btn.click(
            on_create_form,
            inputs=[design_form_name, design_form_desc, design_form_id_state],
            outputs=[design_form_id_state, design_form_dd, design_message, field_list_output]
        )

        update_form_btn.click(
            on_update_form,
            inputs=[design_form_id_state, design_form_name, design_form_desc],
            outputs=[design_form_dd, design_message]
        )

        refresh_design_btn.click(
            lambda: gr.update(choices=self._get_form_choices(), value=None),
            outputs=[design_form_dd]
        )

        design_form_dd.change(
            on_design_form_selected,
            inputs=[design_form_dd],
            outputs=[design_form_id_state, design_form_name, design_form_desc,
                    design_message, field_list_output]
        )

        add_field_btn.click(
            on_add_field,
            inputs=[design_form_id_state, field_label, field_type, field_required,
                    field_desc, field_default, field_options],
            outputs=[field_list_output, design_message, field_label, field_desc,
                    field_default, field_options]
        )

        clear_field_btn.click(
            lambda: ("", "", "", ""),
            outputs=[field_label, field_desc, field_default, field_options]
        )

    def _build_form_management_tab(self):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**选择表单**")
                mgmt_form_dd = gr.Dropdown(label="表单列表", choices=[])
                refresh_mgmt_btn = gr.Button("🔄 刷新列表", variant="secondary", size="sm")
                mgmt_message = gr.Markdown("")

                gr.Markdown("**表单操作**")
                with gr.Row():
                    duplicate_btn = gr.Button("📋 复制表单", variant="secondary", size="sm")
                    delete_btn = gr.Button("🗑️ 删除表单", variant="stop", size="sm")

                gr.Markdown("**保存为模板**")
                save_tpl_name = gr.Textbox(label="模板名称 *", placeholder="请输入模板名称")
                save_template_btn = gr.Button("💾 保存为模板", variant="primary", size="sm")

            with gr.Column(scale=2):
                gr.Markdown("**表单详情**")
                form_detail = gr.Markdown("👈 请先选择一个表单")

                gr.Markdown("**字段列表**")
                mgmt_field_list = gr.Markdown("")

                gr.Markdown("**字段顺序调整**")
                mgmt_field_dd = gr.Dropdown(label="选择要调整的字段", choices=[])
                with gr.Row():
                    move_up_btn = gr.Button("⬆️ 上移", variant="secondary", size="sm")
                    move_down_btn = gr.Button("⬇️ 下移", variant="secondary", size="sm")
                    del_field_btn = gr.Button("🗑️ 删除该字段", variant="stop", size="sm")

        def _format_field_table(fields):
            if not fields:
                return "**该表单暂无字段**"
            md = "| 序号 | 字段标签 | 类型 | 必填 | 描述 |\n|---|---|---|---|---|\n"
            for i, f in enumerate(fields, 1):
                required = "✅" if f["is_required"] else "—"
                type_cn = FIELD_TYPES_CN.get(f["field_type"], f["field_type"])
                desc = (f.get("field_description") or "—")[:40]
                md += f"| {i} | {f['field_label']} | {type_cn} | {required} | {desc} |\n"
            return md

        def on_mgmt_form_selected(form_id):
            if not form_id:
                return "👈 请先选择一个表单", "", gr.update(choices=[]), ""
            form_data = form_manager.get_form_with_fields(form_id)
            if not form_data:
                return "❌ 表单不存在", "", gr.update(choices=[]), ""
            fields = form_data.get("fields", [])
            stats = form_manager.get_form_statistics(form_id)
            detail_md = f"""
### 📄 表单信息
| 属性 | 内容 |
|---|---|
| **ID** | {form_data['id']} |
| **名称** | {form_data['name']} |
| **描述** | {form_data.get('description') or '无'} |
| **创建时间** | {form_data.get('created_at', 'N/A')} |
| **最后更新** | {form_data.get('updated_at', 'N/A')} |
| **字段数量** | {len(fields)} |
| **总填报记录** | {stats['total_submissions']} |
| **必填字段数** | {stats['required_fields']} |
"""
            field_md = _format_field_table(fields)
            field_choices = [(f"[{f['sort_order']}] {f['field_label']}", f["id"]) for f in fields]
            return detail_md, field_md, gr.update(choices=field_choices, value=None), ""

        def on_duplicate(form_id):
            if not form_id:
                return gr.update(), "❌ 请先选择一个表单"
            try:
                new_id = form_manager.duplicate_form(form_id)
                choices = self._get_form_choices()
                return gr.update(choices=choices, value=new_id), f"✅ 表单复制成功！新表单ID: {new_id}"
            except Exception as e:
                return gr.update(), f"❌ 复制失败: {str(e)}"

        def on_delete(form_id):
            if not form_id:
                return gr.update(), "👈 请先选择一个表单", "", gr.update(choices=[]), ""
            try:
                form_data = db.get_form(form_id)
                form_name = form_data["name"] if form_data else "该表单"
                db.delete_form(form_id)
                choices = self._get_form_choices()
                return gr.update(choices=choices, value=None), f"✅ 表单【{form_name}】已删除", "", gr.update(choices=[]), ""
            except Exception as e:
                return gr.update(), f"❌ 删除失败: {str(e)}", "", gr.update(choices=[]), ""

        def on_save_template(form_id, tpl_name):
            if not form_id:
                return "❌ 请先选择一个表单", tpl_name
            try:
                form_manager.save_form_as_template(form_id, tpl_name)
                return f"✅ 模板【{tpl_name}】保存成功！", ""
            except ValueError as e:
                return f"❌ {str(e)}", tpl_name

        def on_move_field(form_id, field_id, direction):
            if not form_id or not field_id:
                return "", gr.update(), "❌ 请先选择表单和字段"
            try:
                form_manager.move_field_order(field_id, direction)
                fields = db.get_fields_by_form(form_id)
                field_md = _format_field_table(fields)
                field_choices = [(f"[{f['sort_order']}] {f['field_label']}", f["id"]) for f in fields]
                return field_md, gr.update(choices=field_choices, value=field_id), f"✅ 字段已{'上移' if direction == 'up' else '下移'}"
            except Exception as e:
                return "", gr.update(), f"❌ 操作失败: {str(e)}"

        def on_delete_field(form_id, field_id):
            if not form_id or not field_id:
                return "", gr.update(), "❌ 请先选择表单和字段"
            try:
                field = db.get_field(field_id)
                field_label = field["field_label"] if field else "该字段"
                db.delete_field(field_id)
                fields = db.get_fields_by_form(form_id)
                field_md = _format_field_table(fields)
                field_choices = [(f"[{f['sort_order']}] {f['field_label']}", f["id"]) for f in fields]
                return field_md, gr.update(choices=field_choices, value=None), f"✅ 字段【{field_label}】已删除"
            except Exception as e:
                return "", gr.update(), f"❌ 删除失败: {str(e)}"

        refresh_mgmt_btn.click(lambda: gr.update(choices=self._get_form_choices(), value=None), outputs=[mgmt_form_dd])
        mgmt_form_dd.change(on_mgmt_form_selected, inputs=[mgmt_form_dd],
                            outputs=[form_detail, mgmt_field_list, mgmt_field_dd, mgmt_message])
        duplicate_btn.click(on_duplicate, inputs=[mgmt_form_dd], outputs=[mgmt_form_dd, mgmt_message])
        delete_btn.click(on_delete, inputs=[mgmt_form_dd],
                         outputs=[mgmt_form_dd, mgmt_message, form_detail, mgmt_field_list, mgmt_field_dd])
        save_template_btn.click(on_save_template, inputs=[mgmt_form_dd, save_tpl_name],
                                outputs=[mgmt_message, save_tpl_name])
        move_up_btn.click(lambda fid, fld: on_move_field(fid, fld, "up"),
                          inputs=[mgmt_form_dd, mgmt_field_dd],
                          outputs=[mgmt_field_list, mgmt_field_dd, mgmt_message])
        move_down_btn.click(lambda fid, fld: on_move_field(fid, fld, "down"),
                            inputs=[mgmt_form_dd, mgmt_field_dd],
                            outputs=[mgmt_field_list, mgmt_field_dd, mgmt_message])
        del_field_btn.click(on_delete_field, inputs=[mgmt_form_dd, mgmt_field_dd],
                            outputs=[mgmt_field_list, mgmt_field_dd, mgmt_message])

    def _build_template_tab(self):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**模板列表**")
                template_dd = gr.Dropdown(label="选择模板", choices=[])
                refresh_tpl_btn = gr.Button("🔄 刷新", variant="secondary", size="sm")
                template_msg = gr.Markdown("")

                gr.Markdown("**模板操作**")
                load_tpl_name = gr.Textbox(label="新表单名称", placeholder="留空则使用默认名称")
                load_tpl_btn = gr.Button("📂 加载为新表单", variant="primary", size="sm")
                delete_tpl_btn = gr.Button("🗑️ 删除模板", variant="stop", size="sm")

            with gr.Column(scale=2):
                gr.Markdown("**模板详情**")
                template_detail = gr.Markdown("👈 请先选择一个模板")

        def _format_field_table(fields):
            if not fields:
                return "**该模板暂无字段定义**"
            md = "| 序号 | 字段标签 | 类型 | 必填 | 描述 |\n|---|---|---|---|---|\n"
            for i, f in enumerate(fields, 1):
                required = "✅" if f.get("is_required") else "—"
                type_cn = FIELD_TYPES_CN.get(f.get("field_type", ""), f.get("field_type", ""))
                desc = (f.get("field_description") or "—")[:40]
                md += f"| {i} | {f.get('field_label', '')} | {type_cn} | {required} | {desc} |\n"
            return md

        def on_template_selected(tpl_id):
            if not tpl_id:
                return "👈 请先选择一个模板", ""
            template = db.get_template(tpl_id)
            if not template:
                return "❌ 模板不存在", ""
            tpl_data = template["template_data"]
            form_info = tpl_data.get("form", {})
            fields = tpl_data.get("fields", [])
            md = f"""
### 📄 模板信息
| 属性 | 内容 |
|---|---|
| **模板ID** | {template['id']} |
| **模板名称** | {template['template_name']} |
| **保存时间** | {template.get('created_at', 'N/A')} |
| **源表单名称** | {form_info.get('name', 'N/A')} |
| **字段数量** | {len(fields)} |

### 📋 字段列表
{_format_field_table(fields)}
"""
            return md, ""

        def on_load_template(tpl_id, new_name):
            if not tpl_id:
                return "❌ 请先选择一个模板", new_name
            try:
                form_id = form_manager.load_template_to_new_form(tpl_id, new_name or None)
                form = db.get_form(form_id)
                return f"✅ 模板加载成功！新表单【{form['name']}】ID: {form_id}", ""
            except Exception as e:
                return f"❌ 加载失败: {str(e)}", new_name

        def on_delete_template(tpl_id):
            if not tpl_id:
                return gr.update(), "👈 请先选择一个模板", ""
            try:
                template = db.get_template(tpl_id)
                tpl_name = template["template_name"] if template else "该模板"
                db.delete_template(tpl_id)
                templates = db.get_all_templates()
                choices = [(f"{t['template_name']} (ID: {t['id']})", t["id"]) for t in templates]
                return gr.update(choices=choices, value=None), "👈 请先选择一个模板", f"✅ 模板【{tpl_name}】已删除"
            except Exception as e:
                return gr.update(), "👈 请先选择一个模板", f"❌ 删除失败: {str(e)}"

        refresh_tpl_btn.click(
            lambda: gr.update(
                choices=[(f"{t['template_name']} (ID: {t['id']})", t["id"]) for t in db.get_all_templates()],
                value=None
            ),
            outputs=[template_dd]
        )
        template_dd.change(on_template_selected, inputs=[template_dd],
                           outputs=[template_detail, template_msg])
        load_tpl_btn.click(on_load_template, inputs=[template_dd, load_tpl_name],
                           outputs=[template_msg, load_tpl_name])
        delete_tpl_btn.click(on_delete_template, inputs=[template_dd],
                             outputs=[template_dd, template_detail, template_msg])

    def _build_data_view_tab(self):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**选择表单**")
                view_form_dd = gr.Dropdown(label="表单列表", choices=[])
                refresh_view_btn = gr.Button("🔄 刷新", variant="secondary", size="sm")
                view_message = gr.Markdown("")

                gr.Markdown("**统计信息**")
                view_stats = gr.Markdown("")

            with gr.Column(scale=2):
                gr.Markdown("**填报记录**")
                view_data_output = gr.Markdown("👈 请先选择一个表单")

        def on_view_form_selected(form_id):
            if not form_id:
                return "👈 请先选择一个表单", "", ""
            try:
                data = form_manager.export_form_data_as_dict(form_id)
                form_info = data["form_info"]
                fields = data["fields"]
                submissions = data["submissions"]
                stats = form_manager.get_form_statistics(form_id)

                stats_md = f"""
| 指标 | 数值 |
|---|---|
| **总记录数** | {stats['total_submissions']} |
| **字段总数** | {stats['total_fields']} |
| **必填字段** | {stats['required_fields']} |
| **最后提交** | {stats.get('last_submission_time') or '暂无'} |
"""
                if not submissions:
                    return "**暂无填报记录**", stats_md, ""

                data_md = f"### 📋 {form_info['name']} - 填报记录 ({len(submissions)}条)\n\n"
                headers = ["提交时间"] + [f["field_label"] for f in fields]
                data_md += "| " + " | ".join(headers) + " |\n"
                data_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                for sub in submissions[:50]:
                    row = [sub["created_at"]]
                    for f in fields:
                        val = sub["submission_data"].get(f["field_name"], "")
                        val_str = str(val)[:50]
                        row.append(val_str.replace("|", "\\|"))
                    data_md += "| " + " | ".join(row) + " |\n"

                if len(submissions) > 50:
                    data_md += f"\n> *仅显示最近50条记录，共{len(submissions)}条*"

                return data_md, stats_md, ""
            except Exception as e:
                return f"❌ 查看失败: {str(e)}", "", ""

        refresh_view_btn.click(lambda: gr.update(choices=self._get_form_choices(), value=None),
                               outputs=[view_form_dd])
        view_form_dd.change(on_view_form_selected, inputs=[view_form_dd],
                            outputs=[view_data_output, view_stats, view_message])


def main():
    app = DataEntryApp()
    demo = app.build_interface()
    print(f"🚀 {APP_TITLE} v{APP_VERSION} 启动中...")
    print("📖 请在浏览器中打开: http://localhost:7860")
    demo.launch(share=False, server_name="0.0.0.0", server_port=7861, show_error=True, theme=gr.themes.Soft(), css=DataEntryApp._CUSTOM_CSS)


if __name__ == "__main__":
    main()
