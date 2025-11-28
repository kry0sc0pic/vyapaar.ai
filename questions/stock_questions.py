questions = [
    # NOTE: -------------------------------eO2-------------------------
    {
            "question": "Based on sales, do I need to restock eggs soon?",
            "template": "Restock recommendation: {value}.",
            "format_type": "text",
            "sql": """
                    /* Logic: Calculate Days of Supply. If < 3 days, return Yes */
                    WITH stats AS (
                        SELECT 
                            p.current_stock,
                            COALESCE(SUM(si.quantity) / 30.0, 0) as daily_sales_rate
                        FROM products p
                        LEFT JOIN sale_items si ON p.product_id = si.product_id
                        LEFT JOIN sales s ON si.sale_id = s.sale_id
                        WHERE p.name_en ILIKE '%Eggs%'
                          AND s.sale_time >= CURRENT_DATE - 30
                        GROUP BY p.product_id, p.current_stock
                    )
                    SELECT 
                        CASE 
                            WHEN daily_sales_rate = 0 THEN 'No (No recent sales)'
                            WHEN (current_stock / daily_sales_rate) < 3 THEN 'Yes (Critical)'
                            ELSE 'No'
                        END
                    FROM stats;
                """
        },
        {
                    "question": "Should I order more bread for tomorrow?",
            "template": "Order recommendation for Bread: {value}.",
            "format_type": "text",
            "sql": """
                    /* Logic: If stock < 1.5 * Average Daily Sales, say Yes */
                    WITH stats AS (
                        SELECT 
                            p.current_stock,
                            COALESCE(SUM(si.quantity) / 30.0, 0) as daily_sales_rate
                        FROM products p
                        LEFT JOIN sale_items si ON p.product_id = si.product_id
                        LEFT JOIN sales s ON si.sale_id = s.sale_id
                        WHERE p.name_en ILIKE '%Bread%'
                          AND s.sale_time >= CURRENT_DATE - 30
                        GROUP BY p.product_id, p.current_stock
                    )
                    SELECT 
                        CASE 
                            WHEN current_stock < (daily_sales_rate * 1.5) THEN 'Yes'
                            ELSE 'No'
                        END
                    FROM stats;
                """
        },
        {
                    "question": "How many units of butter will I need for the weekend?",
            "template": "Estimated Butter demand for full weekend: {value} units.",
            "format_type": "text",
            "sql": """
                    /* Logic: Avg sum of sales on Sat(6)+Sun(7) over last 8 weeks */
                    SELECT ROUND(AVG(weekend_total), 0)
                    FROM (
                        SELECT DATE_TRUNC('week', s.sale_time) as week_start, SUM(si.quantity) as weekend_total
                        FROM sales s
                        JOIN sale_items si ON s.sale_id = si.sale_id
                        JOIN products p ON si.product_id = p.product_id
                        WHERE p.name_en ILIKE '%Butter%'
                          AND EXTRACT(ISODOW FROM s.sale_time) IN (6, 7) -- Sat, Sun
                          AND s.sale_time >= CURRENT_DATE - INTERVAL '8 weeks'
                        GROUP BY week_start
                    ) sub;
                """
        },
        {
                    "question": "When will my current milk stock run out at the current sales rate?",
            "template": "Milk stock will last approximately {value} days.",
            "format_type": "text",
            "sql": """
                    /* Logic: Sum of Stock (All Milk) / Sum of Daily Rate (All Milk) */
                    WITH milk_stats AS (
                        SELECT 
                            SUM(p.current_stock) as total_stock,
                            SUM(si.quantity) / 30.0 as combined_daily_rate
                        FROM products p
                        JOIN sale_items si ON p.product_id = si.product_id
                        JOIN sales s ON si.sale_id = s.sale_id
                        WHERE (p.name_en ILIKE '%Milk%' OR p.name_en ILIKE '%Doodh%' OR p.category = 'Dairy')
                          AND p.unit = 'packet' -- Excluding eggs/butter based on seed data
                          AND s.sale_time >= CURRENT_DATE - 30
                    )
                    SELECT ROUND(total_stock / NULLIF(combined_daily_rate, 0), 1)
                    FROM milk_stats;
                """
        },
        {
                    "question": "Which product needs urgent restocking?",
            "template": "Most urgent item: {value}.",
            "format_type": "text",
            "sql": """
                    /* Logic: Lowest Days-On-Hand (Stock / Daily Rate) */
                    SELECT p.name_en
                    FROM products p
                    JOIN (
                        SELECT product_id, SUM(quantity)/30.0 as daily_rate
                        FROM sale_items si 
                        JOIN sales s ON si.sale_id = s.sale_id
                        WHERE s.sale_time >= CURRENT_DATE - 30
                        GROUP BY product_id
                    ) stats ON p.product_id = stats.product_id
                    ORDER BY (p.current_stock / NULLIF(stats.daily_rate, 0)) ASC
                    LIMIT 1;
                """
        },
        {
                    "question": "Which item will last the longest based on current sales?",
            "template": "Longest lasting item: {value}.",
            "format_type": "text",
            "sql": """
                    /* Logic: Highest Days-On-Hand */
                    SELECT p.name_en
                    FROM products p
                    JOIN (
                        SELECT product_id, SUM(quantity)/30.0 as daily_rate
                        FROM sale_items si 
                        JOIN sales s ON si.sale_id = s.sale_id
                        WHERE s.sale_time >= CURRENT_DATE - 30
                        GROUP BY product_id
                    ) stats ON p.product_id = stats.product_id
                    ORDER BY (p.current_stock / NULLIF(stats.daily_rate, 0)) DESC
                    LIMIT 1;
                """
        },
        {
                    "question": "Are weekend milk sales higher than weekdays?",
            "template": "Are weekend sales higher? {value}.",
            "format_type": "text",
            "sql": """
                    /* Logic: Compare Avg Daily Sales (Sat/Sun) vs (Mon-Fri) */
                    WITH daily_avgs AS (
                        SELECT 
                            CASE WHEN EXTRACT(ISODOW FROM s.sale_time) IN (6, 7) THEN 'Weekend' ELSE 'Weekday' END as day_type,
                            COUNT(DISTINCT DATE(s.sale_time)) as days_count,
                            SUM(si.quantity) as total_qty
                        FROM sale_items si
                        JOIN sales s ON si.sale_id = s.sale_id
                        JOIN products p ON si.product_id = p.product_id
                        WHERE p.name_en ILIKE '%Milk%'
                          AND s.sale_time >= CURRENT_DATE - 90
                        GROUP BY 1
                    )
                    SELECT 
                        CASE 
                            WHEN (SELECT total_qty::float/days_count FROM daily_avgs WHERE day_type='Weekend') > 
                                 (SELECT total_qty::float/days_count FROM daily_avgs WHERE day_type='Weekday') 
                            THEN 'Yes' 
                            ELSE 'No' 
                        END;
                """
        },
        {
                    "question": "How much stock did eggs reduce this week?",
            "template": "Eggs sold in the last 7 days: {value} units.",
            "format_type": "text",
            "sql": """
                    SELECT COALESCE(SUM(si.quantity), 0)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.sale_id
                    JOIN products p ON si.product_id = p.product_id
                    WHERE p.name_en ILIKE '%Eggs%'
                      AND s.sale_time >= CURRENT_DATE - 7;
                """
        },
        {
                    "question": "How quickly does bread sell out on average?",
            "template": "Average sales velocity: {value} packets per day.",
            "format_type": "text",
            "sql": """
                    SELECT ROUND(SUM(si.quantity) / 30.0, 1)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.sale_id
                    JOIN products p ON si.product_id = p.product_id
                    WHERE p.name_en ILIKE '%Bread%'
                      AND s.sale_time >= CURRENT_DATE - 30;
                """
        },
        {
                    "question": "What is my weekly demand for milk?",
            "template": "Average weekly demand: {value} packets.",
            "format_type": "text",
            "sql": """
                    /* Logic: Calculate daily rate * 7 */
                    SELECT ROUND((SUM(si.quantity) / 90.0) * 7, 0)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.sale_id
                    JOIN products p ON si.product_id = p.product_id
                    WHERE p.name_en ILIKE '%Milk%'
                      AND s.sale_time >= CURRENT_DATE - 90;
                """
        }
]
