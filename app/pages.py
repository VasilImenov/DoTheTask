
from flask import Blueprint, render_template, request, redirect, url_for
from .db import get_db, query

bp = Blueprint("pages", __name__)



@bp.route("/")
def index():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "all")
    priority = request.args.get("priority", "all")
    sort = request.args.get("sort", "newest")

    
    sql = """
        SELECT tasks.id, tasks.title, tasks.description,
            tasks.priority, tasks.due_date, tasks.completed,
            categories.name AS category,
            (
               tasks.due_date < CURRENT_DATE
               AND tasks.completed = FALSE
            ) AS is_overdue
        FROM tasks
        LEFT JOIN categories ON tasks.category_id = categories.id
        WHERE 1=1
    """

    params = []

    if search:
        sql += " AND (tasks.title ILIKE %s OR tasks.description ILIKE %s)"
        params.extend(["%" + search + "%", "%" + search + "%"])

    if status == "active":
        sql += " AND tasks.completed = FALSE"
    elif status == "completed":
        sql += " AND tasks.completed = TRUE"

    if priority in ("low", "medium", "high"):
        sql += " AND tasks.priority = %s"
        params.append(priority)

    if sort == "oldest":
        sql += " ORDER BY tasks.id ASC"
    elif sort == "due_date":
        sql += " ORDER BY tasks.due_date ASC NULLS LAST, tasks.id DESC"
    elif sort == "priority":
        sql += """
            ORDER BY CASE tasks.priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END, tasks.id DESC
        """
    else:
        sql += " ORDER BY tasks.id DESC"

    tasks = query(sql, tuple(params))
    categories = query("SELECT * FROM categories ORDER BY name")
    stats = query("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE completed = FALSE
            ) AS active,
            COUNT(*) FILTER (
                WHERE completed = TRUE
            ) AS completed,
            COUNT(*) FILTER (
                WHERE completed = FALSE
                AND due_date < CURRENT_DATE
            ) AS overdue
        FROM tasks
    """, one=True)

    return render_template(
        "index.html",
        tasks=tasks,
        categories=categories,
        search=search,
        status=status,
        priority=priority,
        sort=sort,
        stats=stats
    )

@bp.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "medium")
    due_date = request.form.get("due_date") or None
    category_id = request.form.get("category_id") or None

    if not title:
        return redirect(url_for("pages.index"))

    if priority not in ("low", "medium", "high"):
        priority = "medium"

    db = get_db()

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO tasks
            (title, description, priority, due_date, category_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, priority, due_date, category_id))

    db.commit()

    return redirect(url_for("pages.index"))

@bp.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET completed = NOT completed
            WHERE id = %s
        """, (task_id,))

    db.commit()

    return redirect(url_for("pages.index"))

@bp.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )

    db.commit()

    return redirect(url_for("pages.index"))

@bp.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = query(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,),
        one=True
    )

    if task is None:
        return "Задачата не е намерена", 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "medium")
        due_date = request.form.get("due_date") or None
        category_id = request.form.get("category_id") or None

        if not title:
            return "Заглавието е задължително", 400

        if priority not in ("low", "medium", "high"):
            return "Невалиден приоритет", 400

        db = get_db()

        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE tasks
                SET title = %s,
                    description = %s,
                    priority = %s,
                    due_date = %s,
                    category_id = %s
                WHERE id = %s
            """, (
                title, description, priority,
                due_date, category_id, task_id
            ))

        db.commit()

        return redirect(url_for("pages.index"))

    categories = query(
        "SELECT * FROM categories ORDER BY name"
    )

    return render_template(
        "edit.html",
        task=task,
        categories=categories
    )

@bp.route("/categories", methods=["GET"])
def categories_page():
    categories = query("""
        SELECT categories.id, categories.name,
               COUNT(tasks.id) AS task_count
        FROM categories
        LEFT JOIN tasks ON tasks.category_id = categories.id
        GROUP BY categories.id, categories.name
        ORDER BY categories.name
    """)

    return render_template(
        "categories.html",
        categories=categories
    )


@bp.route("/categories/add", methods=["POST"])
def add_category():
    name = request.form.get("name", "").strip()

    if not name or len(name) > 50:
        return redirect(url_for("pages.categories_page"))

    db = get_db()

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO categories (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (name,))

    db.commit()

    return redirect(url_for("pages.categories_page"))


@bp.route("/categories/delete/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute(
            "DELETE FROM categories WHERE id = %s",
            (category_id,)
        )

    db.commit()

    return redirect(url_for("pages.categories_page"))
