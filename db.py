import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_directory()
        self._initialize_database()

    def _ensure_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_database(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    field_label TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    is_required INTEGER DEFAULT 0,
                    field_options TEXT,
                    field_description TEXT,
                    default_value TEXT,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_id INTEGER NOT NULL,
                    submission_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL,
                    template_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("PRAGMA foreign_keys = ON")

    def create_form(self, name, description=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO forms (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, description, now, now)
            )
            return cursor.lastrowid

    def update_form(self, form_id, name, description=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE forms SET name=?, description=?, updated_at=? WHERE id=?",
                (name, description, now, form_id)
            )
            return cursor.rowcount > 0

    def delete_form(self, form_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM form_fields WHERE form_id=?", (form_id,))
            cursor.execute("DELETE FROM submissions WHERE form_id=?", (form_id,))
            cursor.execute("DELETE FROM forms WHERE id=?", (form_id,))
            return cursor.rowcount > 0

    def get_form(self, form_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM forms WHERE id=?", (form_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_forms(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM forms ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_field(self, form_id, field_name, field_label, field_type,
                  is_required=False, field_options=None, field_description=None,
                  default_value=None, sort_order=0):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        options_json = json.dumps(field_options) if field_options else None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO form_fields (form_id, field_name, field_label, field_type,
                   is_required, field_options, field_description, default_value, sort_order, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (form_id, field_name, field_label, field_type,
                 1 if is_required else 0, options_json, field_description,
                 default_value, sort_order, now)
            )
            return cursor.lastrowid

    def update_field(self, field_id, field_name=None, field_label=None, field_type=None,
                     is_required=None, field_options=None, field_description=None,
                     default_value=None, sort_order=None):
        fields = []
        values = []
        if field_name is not None:
            fields.append("field_name=?")
            values.append(field_name)
        if field_label is not None:
            fields.append("field_label=?")
            values.append(field_label)
        if field_type is not None:
            fields.append("field_type=?")
            values.append(field_type)
        if is_required is not None:
            fields.append("is_required=?")
            values.append(1 if is_required else 0)
        if field_options is not None:
            fields.append("field_options=?")
            values.append(json.dumps(field_options) if field_options else None)
        if field_description is not None:
            fields.append("field_description=?")
            values.append(field_description)
        if default_value is not None:
            fields.append("default_value=?")
            values.append(default_value)
        if sort_order is not None:
            fields.append("sort_order=?")
            values.append(sort_order)

        if not fields:
            return False

        values.append(field_id)
        query = f"UPDATE form_fields SET {', '.join(fields)} WHERE id=?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            return cursor.rowcount > 0

    def delete_field(self, field_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM form_fields WHERE id=?", (field_id,))
            return cursor.rowcount > 0

    def get_fields_by_form(self, form_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM form_fields WHERE form_id=? ORDER BY sort_order, id",
                (form_id,)
            )
            fields = []
            for row in cursor.fetchall():
                field = dict(row)
                if field.get("field_options"):
                    field["field_options"] = json.loads(field["field_options"])
                fields.append(field)
            return fields

    def get_field(self, field_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM form_fields WHERE id=?", (field_id,))
            row = cursor.fetchone()
            if row:
                field = dict(row)
                if field.get("field_options"):
                    field["field_options"] = json.loads(field["field_options"])
                return field
            return None

    def save_submission(self, form_id, submission_data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_json = json.dumps(submission_data, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO submissions (form_id, submission_data, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (form_id, data_json, now, now)
            )
            return cursor.lastrowid

    def update_submission(self, submission_id, submission_data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_json = json.dumps(submission_data, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE submissions SET submission_data=?, updated_at=? WHERE id=?",
                (data_json, now, submission_id)
            )
            return cursor.rowcount > 0

    def get_submissions_by_form(self, form_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM submissions WHERE form_id=? ORDER BY created_at DESC",
                (form_id,)
            )
            submissions = []
            for row in cursor.fetchall():
                sub = dict(row)
                sub["submission_data"] = json.loads(sub["submission_data"])
                submissions.append(sub)
            return submissions

    def get_submission(self, submission_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE id=?", (submission_id,))
            row = cursor.fetchone()
            if row:
                sub = dict(row)
                sub["submission_data"] = json.loads(sub["submission_data"])
                return sub
            return None

    def delete_submission(self, submission_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM submissions WHERE id=?", (submission_id,))
            return cursor.rowcount > 0

    def save_template(self, template_name, form_data, fields_data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template_data = json.dumps({
            "form": form_data,
            "fields": fields_data
        }, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO form_templates (template_name, template_data, created_at) VALUES (?, ?, ?)",
                (template_name, template_data, now)
            )
            return cursor.lastrowid

    def get_all_templates(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, template_name, created_at FROM form_templates ORDER BY created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_template(self, template_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM form_templates WHERE id=?", (template_id,))
            row = cursor.fetchone()
            if row:
                tpl = dict(row)
                tpl["template_data"] = json.loads(tpl["template_data"])
                return tpl
            return None

    def delete_template(self, template_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM form_templates WHERE id=?", (template_id,))
            return cursor.rowcount > 0

    def load_template_to_form(self, template_id, new_form_name=None):
        template = self.get_template(template_id)
        if not template:
            return None

        template_data = template["template_data"]
        form_info = template_data["form"]
        fields_info = template_data["fields"]

        form_name = new_form_name or f"{form_info.get('name', template['template_name'])} (副本)"
        form_id = self.create_form(form_name, form_info.get("description"))

        for field in fields_info:
            self.add_field(
                form_id=form_id,
                field_name=field.get("field_name"),
                field_label=field.get("field_label"),
                field_type=field.get("field_type", "text"),
                is_required=field.get("is_required", False),
                field_options=field.get("field_options"),
                field_description=field.get("field_description"),
                default_value=field.get("default_value"),
                sort_order=field.get("sort_order", 0)
            )

        return form_id


db = DatabaseManager()
