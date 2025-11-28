questions = [
    # NOTE: ---------------EO1-----------------------------
    {
        "question": "Did my eggs sales improve compared to last week?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as cur_val,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '14 days' AND s.sale_time < CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as prev_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Eggs%'
            )
            SELECT
                CASE
                    WHEN cur_val > prev_val THEN 'Yes, sales improved (Current Week: ₹' || to_char(cur_val, 'FM99,999.00') || ' vs Previous: ₹' || to_char(prev_val, 'FM99,999.00') || ')'
                    WHEN cur_val < prev_val THEN 'No, sales declined (Current Week: ₹' || to_char(cur_val, 'FM99,999.00') || ' vs Previous: ₹' || to_char(prev_val, 'FM99,999.00') || ')'
                    ELSE 'No change in sales.'
                END
            FROM stats;
        """
    },
    {
        "question": "Are bread sales increasing compared to last month?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '30 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as cur_val,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '60 days' AND s.sale_time < CURRENT_DATE - INTERVAL '30 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as prev_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Bread%'
            )
            SELECT
                CASE
                    WHEN cur_val > prev_val THEN 'Yes, increasing (Last 30 Days: ₹' || to_char(cur_val, 'FM99,999.00') || ' vs Prior 30 Days: ₹' || to_char(prev_val, 'FM99,999.00') || ')'
                    ELSE 'No, not increasing (Last 30 Days: ₹' || to_char(cur_val, 'FM99,999.00') || ' vs Prior 30 Days: ₹' || to_char(prev_val, 'FM99,999.00') || ')'
                END
            FROM stats;
        """
    },
    {
        "question": "How do butter sales today compare with yesterday?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN DATE(s.sale_time) = CURRENT_DATE THEN si.quantity * si.sold_price ELSE 0 END), 0) as today_val,
                    COALESCE(SUM(CASE WHEN DATE(s.sale_time) = CURRENT_DATE - 1 THEN si.quantity * si.sold_price ELSE 0 END), 0) as yest_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Butter%'
            )
            SELECT 'Today: ₹' || to_char(today_val, 'FM99,999.00') || ' vs Yesterday: ₹' || to_char(yest_val, 'FM99,999.00')
            FROM stats;
        """
    },
    {
        "question": "Is Mother Dairy milk selling better than Amul milk this week?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN p.name_en ILIKE '%Mother Dairy%' THEN si.quantity * si.sold_price ELSE 0 END), 0) as md_val,
                    COALESCE(SUM(CASE WHEN p.name_en ILIKE '%Amul%' AND p.name_en ILIKE '%Milk%' THEN si.quantity * si.sold_price ELSE 0 END), 0) as amul_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE s.sale_time >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT
                CASE
                    WHEN md_val > amul_val THEN 'Yes, Mother Dairy (₹' || to_char(md_val, 'FM99,999') || ') is higher than Amul (₹' || to_char(amul_val, 'FM99,999') || ').'
                    ELSE 'No, Amul (₹' || to_char(amul_val, 'FM99,999') || ') is higher than Mother Dairy (₹' || to_char(md_val, 'FM99,999') || ').'
                END
            FROM stats;
        """
    },
    {
        "question": "Are my total sales higher this month than last month?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
             WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '30 days' THEN s.total_amount ELSE 0 END), 0) as cur_val,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '60 days' AND s.sale_time < CURRENT_DATE - INTERVAL '30 days' THEN s.total_amount ELSE 0 END), 0) as prev_val
                FROM sales s
            )
            SELECT
                CASE
                    WHEN cur_val > prev_val THEN 'Yes, higher (₹' || to_char(cur_val, 'FM99,999') || ' vs ₹' || to_char(prev_val, 'FM99,999') || ')'
                    ELSE 'No, lower (₹' || to_char(cur_val, 'FM99,999') || ' vs ₹' || to_char(prev_val, 'FM99,999') || ')'
                END
            FROM stats;
        """
    },
    {
        "question": "Are eggs sales trending up or down?",
        "template": "Eggs sales are {value}.",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as cur_val,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '14 days' AND s.sale_time < CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as prev_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Eggs%'
            )
            SELECT
                CASE
                    WHEN cur_val > prev_val THEN 'trending up'
                    WHEN cur_val < prev_val THEN 'trending down'
                    ELSE 'stable'
                END
            FROM stats;
        """
    },
    {
        "question": "How do this week’s sales compare to last week’s?",
        "template": "{value}",
        "format_type": "text",
        "sql": """
             WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '7 days' THEN s.total_amount ELSE 0 END), 0) as cur_val,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '14 days' AND s.sale_time < CURRENT_DATE - INTERVAL '7 days' THEN s.total_amount ELSE 0 END), 0) as prev_val
                FROM sales s
            )
            SELECT 'This Week: ₹' || to_char(cur_val, 'FM99,999') || ' vs Last Week: ₹' || to_char(prev_val, 'FM99,999')
            FROM stats;
        """
    },
    {
        "question": "Which product grew the fastest this month?",
        "template": "The fastest growing product was {value}.",
        "format_type": "text",
        "sql": """
            WITH product_stats AS (
                SELECT
                    p.name_en,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '30 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as cur_sales,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '60 days' AND s.sale_time < CURRENT_DATE - INTERVAL '30 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as prev_sales
                FROM products p
                JOIN sale_items si ON p.product_id = si.product_id
                JOIN sales s ON si.sale_id = s.sale_id
                GROUP BY p.name_en
            )
            SELECT name_en || ' (Growth: ' || TO_CHAR(((cur_sales - prev_sales) / NULLIF(prev_sales, 0)) * 100, 'FM999.0') || '%)'
            FROM product_stats
            ORDER BY ((cur_sales - prev_sales) / NULLIF(prev_sales, 0)) DESC NULLS LAST
            LIMIT 1;
        """
    },
    {
        "question": "Which item saw the biggest drop this week?",
        "template": "The item with the biggest drop was {value}.",
        "format_type": "text",
        "sql": """
             WITH product_stats AS (
                SELECT
                    p.name_en,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as cur_sales,
                    COALESCE(SUM(CASE WHEN s.sale_time >= CURRENT_DATE - INTERVAL '14 days' AND s.sale_time < CURRENT_DATE - INTERVAL '7 days' THEN si.quantity * si.sold_price ELSE 0 END), 0) as prev_sales
                FROM products p
                JOIN sale_items si ON p.product_id = si.product_id
                JOIN sales s ON si.sale_id = s.sale_id
                GROUP BY p.name_en
            )
            SELECT name_en || ' (Drop: ₹' || TO_CHAR(prev_sales - cur_sales, 'FM99,999') || ')'
            FROM product_stats
            ORDER BY (prev_sales - cur_sales) DESC NULLS LAST
            LIMIT 1;
        """
    },
    {
        "question": "Compare milk sales between yesterday and today.",
        "template": "{value}",
        "format_type": "text",
        "sql": """
            WITH stats AS (
                SELECT
                    COALESCE(SUM(CASE WHEN DATE(s.sale_time) = CURRENT_DATE THEN si.quantity * si.sold_price ELSE 0 END), 0) as today_val,
                    COALESCE(SUM(CASE WHEN DATE(s.sale_time) = CURRENT_DATE - 1 THEN si.quantity * si.sold_price ELSE 0 END), 0) as yest_val
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.category = 'Dairy' AND p.unit = 'packet' -- Filter for Milk packets
            )
            SELECT 'Today: ₹' || to_char(today_val, 'FM99,999.00') || ' vs Yesterday: ₹' || to_char(yest_val, 'FM99,999.00')
            FROM stats;
        """
    }
]
