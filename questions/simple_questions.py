questions = [
    {
        "question": "What were my eggs sales yesterday?",
        "template": "Eggs sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            AND p.name_en ILIKE '%Eggs%';
        """
    },
    {
        "question": "What were my bread sales yesterday?",
        "template": "Bread sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            AND p.name_en ILIKE '%Bread%';
        """
    },
    {
        "question": "What were my butter sales yesterday?",
        "template": "Butter sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            AND p.name_en ILIKE '%Butter%';
        """
    },
    {
        "question": "What were my Mother Dairy milk sales yesterday?",
        "template": "Mother Dairy milk sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            AND p.name_en ILIKE '%Mother Dairy%';
        """
    },
    {
        "question": "What were my Amul milk sales yesterday?",
        "template": "Amul milk sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            AND p.name_en ILIKE '%Amul Taaza Milk%';
        """
    },
    {
        "question": "What were my total sales yesterday?",
        "template": "Total sales yesterday were {value}.",
        "format_type": "currency",
        "sql": """
            SELECT COALESCE(SUM(si.quantity * si.sold_price), 0)
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1;
        """
    },
    {
        "question": "Which item sold the most yesterday?",
        "template": "The item that sold the most yesterday was {value}.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) DESC
            LIMIT 1;
        """
    },
    {
        "question": "Which item sold the least yesterday?",
        "template": "The item that sold the least yesterday was {value}.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE DATE(s.sale_time) = CURRENT_DATE - 1
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) ASC
            LIMIT 1;
        """
    },
    {
        "question": "Which are the top 5 selling items?",
        "template": "The top five selling items are: {value}.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) DESC
            LIMIT 5;
        """
    }
]
