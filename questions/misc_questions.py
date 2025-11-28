questions = [
    # NOTE: --------------------EO4-------------------
{
        "question": "Are my overall sales improving?",
        "template": "Sales growth over the last 30 days is {value}.",
        "format_type": "text",
        "sql": """
            WITH current_period AS (
                SELECT COALESCE(SUM(total_amount), 0) as sales 
                FROM sales 
                WHERE sale_time >= CURRENT_DATE - INTERVAL '30 days'
            ),
            previous_period AS (
                SELECT COALESCE(SUM(total_amount), 0) as sales 
                FROM sales 
                WHERE sale_time < CURRENT_DATE - INTERVAL '30 days' 
                  AND sale_time >= CURRENT_DATE - INTERVAL '60 days'
            )
            SELECT 
                CASE 
                    WHEN p.sales = 0 THEN 'N/A (No previous data)'
                    ELSE CONCAT(ROUND(((c.sales - p.sales) / p.sales) * 100, 1), '%')
                END
            FROM current_period c, previous_period p;
        """
    },
    {
        "question": "What was my best sales day this month?",
        "template": "Your best sales day this month was {value}.",
        "format_type": "text",
        "sql": """
            SELECT TO_CHAR(DATE(sale_time), 'YYYY-MM-DD')
            FROM sales
            WHERE DATE_TRUNC('month', sale_time) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY DATE(sale_time)
            ORDER BY SUM(total_amount) DESC
            LIMIT 1;
        """
    },
    {
        "question": "What was my worst sales day this month?",
        "template": "Your worst sales day this month was {value}.",
        "format_type": "text",
        "sql": """
            SELECT TO_CHAR(DATE(sale_time), 'YYYY-MM-DD')
            FROM sales
            WHERE DATE_TRUNC('month', sale_time) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY DATE(sale_time)
            ORDER BY SUM(total_amount) ASC
            LIMIT 1;
        """
    },
    {
        "question": "What percentage of sales comes from milk?",
        "template": "Milk accounts for {value} of total sales.",
        "format_type": "text",
        "sql": """
            SELECT CONCAT(ROUND((SUM(CASE WHEN p.name_en ILIKE '%Milk%' OR p.name_en ILIKE '%Cream%' THEN si.quantity * si.sold_price ELSE 0 END) / NULLIF(SUM(si.quantity * si.sold_price), 0)) * 100, 1), '%')
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id;
        """
    },
    {
        "question": "What percentage of sales comes from eggs?",
        "template": "Eggs account for {value} of total sales.",
        "format_type": "text",
        "sql": """
            SELECT CONCAT(ROUND((SUM(CASE WHEN p.name_en ILIKE '%Eggs%' THEN si.quantity * si.sold_price ELSE 0 END) / NULLIF(SUM(si.quantity * si.sold_price), 0)) * 100, 1), '%')
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id;
        """
    },
    {
        "question": "What is my average daily revenue?",
        "template": "Your average daily revenue is {value}.",
        "format_type": "currency",
        "sql": """
            SELECT AVG(daily_total)
            FROM (
                SELECT DATE(sale_time), SUM(total_amount) as daily_total
                FROM sales
                GROUP BY DATE(sale_time)
            ) sub;
        """
    },
    {
        "question": "What is my average weekly revenue?",
        "template": "Your average weekly revenue is {value}.",
        "format_type": "currency",
        "sql": """
            SELECT AVG(weekly_total)
            FROM (
                SELECT DATE_TRUNC('week', sale_time), SUM(total_amount) as weekly_total
                FROM sales
                GROUP BY DATE_TRUNC('week', sale_time)
            ) sub;
        """
    },
    {
        "question": "What’s the revenue split between dairy and non-dairy?",
        "template": "The revenue split is: {value}.",
        "format_type": "text",
        "sql": """
            SELECT 
                CONCAT(
                    'Dairy: ', 
                    ROUND((SUM(CASE WHEN p.category = 'Dairy' THEN si.quantity * si.sold_price ELSE 0 END) / NULLIF(SUM(si.quantity * si.sold_price), 0)) * 100, 1), 
                    '%, Non-Dairy: ', 
                    ROUND((SUM(CASE WHEN p.category != 'Dairy' THEN si.quantity * si.sold_price ELSE 0 END) / NULLIF(SUM(si.quantity * si.sold_price), 0)) * 100, 1), 
                    '%'
                )
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id;
        """
    },
    {
        "question": "What is the total number of items sold this week?",
        "template": "You have sold {value} items this week.",
        "format_type": "text",
        "sql": """
            SELECT COALESCE(SUM(si.quantity), 0)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE DATE_TRUNC('week', s.sale_time) = DATE_TRUNC('week', CURRENT_DATE);
        """
    },
    {
        "question": "Give me a summary of today’s sales across all items.",
        "template": "Today's summary: {value}",
        "format_type": "text",
        "sql": """
            SELECT COALESCE(STRING_AGG(CONCAT(name_en, ': ', total_qty, ' units'), ', '), 'No sales today')
            FROM (
                SELECT p.name_en, SUM(si.quantity) as total_qty
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE DATE(s.sale_time) = CURRENT_DATE
                GROUP BY p.name_en
            ) sub;
                    """
    }
]
