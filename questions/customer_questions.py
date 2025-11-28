questions = [
    # NOTE: --------------------EO3--------------
        {
        "question": "Which item customers buy the most in mornings?",
        "template": "Customers buy {value} the most in the mornings.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            -- Morning defined as 8 AM to 11:59 AM
            WHERE EXTRACT(HOUR FROM s.sale_time) >= 8 
            AND EXTRACT(HOUR FROM s.sale_time) < 12
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) DESC
            LIMIT 1;
        """
    },
    {
        "question": "What sells the most in evenings?",
        "template": "{value} is the best seller in the evenings.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            -- Evening defined as 5 PM (17:00) onwards
            WHERE EXTRACT(HOUR FROM s.sale_time) >= 17
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) DESC
            LIMIT 1;
        """
    },
    {
        "question": "Are milk sales higher on weekends?",
        "template": "The answer is {value}.",
        "format_type": "text",
        "sql": """
            WITH daily_avgs AS (
                SELECT 
                    CASE WHEN EXTRACT(DOW FROM s.sale_time) IN (0, 6) THEN 'weekend' ELSE 'weekday' END as day_type,
                    SUM(si.quantity)::numeric / COUNT(DISTINCT DATE(s.sale_time)) as avg_qty_per_day
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.category = 'Dairy' AND (p.name_en ILIKE '%Milk%' OR p.name_en ILIKE '%Full Cream%')
                GROUP BY 1
            )
            SELECT 
                CASE 
                    WHEN (SELECT avg_qty_per_day FROM daily_avgs WHERE day_type = 'weekend') > 
                         (SELECT avg_qty_per_day FROM daily_avgs WHERE day_type = 'weekday') 
                    THEN 'Yes (Weekend Avg is higher)' 
                    ELSE 'No (Weekday Avg is higher)' 
                END;
        """
    },
    {
        "question": "Do bread sales drop midweek?",
        "template": "{value}.",
        "format_type": "text",
        "sql": """
            WITH mid_vs_rest AS (
                SELECT 
                    -- Midweek defined as Tue(2), Wed(3), Thu(4)
                    CASE WHEN EXTRACT(DOW FROM s.sale_time) IN (2, 3, 4) THEN 'midweek' ELSE 'other' END as period,
                    SUM(si.quantity)::numeric / COUNT(DISTINCT DATE(s.sale_time)) as daily_avg
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Bread%'
                GROUP BY 1
            )
            SELECT 
                CASE 
                    WHEN (SELECT daily_avg FROM mid_vs_rest WHERE period = 'midweek') < 
                         (SELECT daily_avg FROM mid_vs_rest WHERE period = 'other')
                    THEN 'Yes, sales drop midweek'
                    ELSE 'No, sales remain steady or higher'
                END;
        """
    },
    {
        "question": "What time of day do eggs sell most?",
        "template": "Eggs sell the most around {value}.",
        "format_type": "text",
        "sql": """
            SELECT TO_CHAR(s.sale_time, 'HH12 AM')
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE p.name_en ILIKE '%Eggs%'
            GROUP BY EXTRACT(HOUR FROM s.sale_time), TO_CHAR(s.sale_time, 'HH12 AM')
            ORDER BY SUM(si.quantity) DESC
            LIMIT 1;
        """
    },
    {
        "question": "Are customers buying more dairy this month?",
        "template": "{value} compared to last month.",
        "format_type": "text",
        "sql": """
            WITH monthly_sales AS (
                SELECT 
                    DATE_TRUNC('month', s.sale_time) as mth,
                    SUM(si.quantity) as total_qty
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.category = 'Dairy'
                AND s.sale_time >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                GROUP BY 1
            )
            SELECT 
                CASE 
                    WHEN 
                        (SELECT total_qty FROM monthly_sales WHERE mth = DATE_TRUNC('month', CURRENT_DATE)) >
                        (SELECT total_qty FROM monthly_sales WHERE mth = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'))
                    THEN 'Yes, sales increased'
                    ELSE 'No, sales are lower'
                END;
        """
    },
    {
        "question": "Are people buying more bread than last month?",
        "template": "{value} compared to last month.",
        "format_type": "text",
        "sql": """
            WITH monthly_sales AS (
                SELECT 
                    DATE_TRUNC('month', s.sale_time) as mth,
                    SUM(si.quantity) as total_qty
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                WHERE p.name_en ILIKE '%Bread%'
                AND s.sale_time >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                GROUP BY 1
            )
            SELECT 
                CASE 
                    WHEN 
                        COALESCE((SELECT total_qty FROM monthly_sales WHERE mth = DATE_TRUNC('month', CURRENT_DATE)), 0) >
                        COALESCE((SELECT total_qty FROM monthly_sales WHERE mth = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')), 0)
                    THEN 'Yes, bread sales are up'
                    ELSE 'No, bread sales are down'
                END;
        """
    },
    {
        "question": "Which item is trending upward this week?",
        "template": "{value} is seeing the highest growth this week.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE s.sale_time >= CURRENT_DATE - INTERVAL '14 days'
            GROUP BY p.name_en
            -- Calculate growth: (Last 7 days) - (7 days before that)
            ORDER BY 
                (SUM(si.quantity) FILTER (WHERE s.sale_time >= CURRENT_DATE - INTERVAL '7 days')) - 
                (SUM(si.quantity) FILTER (WHERE s.sale_time < CURRENT_DATE - INTERVAL '7 days')) DESC
            LIMIT 1;
        """
    },
    {
        "question": "Which item is consistently slow-selling?",
        "template": "The {value} has the lowest total sales volume.",
        "format_type": "text",
        "sql": """
            SELECT p.name_en
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            GROUP BY p.name_en
            ORDER BY SUM(si.quantity) ASC
            LIMIT 1;
        """
    },
    {
        "question": "What is my peak sales hour?",
        "template": "Your peak sales hour is {value}.",
        "format_type": "text",
        "sql": """
        SELECT TO_CHAR(MIN(s.sale_time), 'HH12 AM') || ' - ' || TO_CHAR(MIN(s.sale_time) + INTERVAL '1 hour', 'HH12 AM')
                    FROM sales s
                                GROUP BY EXTRACT(HOUR FROM s.sale_time)
                                            ORDER BY SUM(s.total_amount) DESC
                                                        LIMIT 1;"""
    }

]
