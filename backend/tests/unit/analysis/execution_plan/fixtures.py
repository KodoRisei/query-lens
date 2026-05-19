"""
Sample EXPLAIN JSON payloads mirroring real PostgreSQL output.
Used by tests to avoid requiring a live database.
"""

SEQ_SCAN_LARGE = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Alias": "users",
        "Startup Cost": 0.00,
        "Total Cost": 1540.00,
        "Plan Rows": 10000,
        "Plan Width": 80,
        "Actual Startup Time": 0.012,
        "Actual Total Time": 45.6,
        "Actual Rows": 9876,
        "Actual Loops": 1,
        "Shared Hit Blocks": 500,
        "Shared Read Blocks": 234,
    },
    "Planning Time": 0.5,
    "Execution Time": 46.1,
}

SEQ_SCAN_SMALL = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "config",
        "Alias": "config",
        "Startup Cost": 0.00,
        "Total Cost": 1.05,
        "Plan Rows": 5,
        "Plan Width": 40,
        "Actual Startup Time": 0.001,
        "Actual Total Time": 0.005,
        "Actual Rows": 5,
        "Actual Loops": 1,
        "Shared Hit Blocks": 1,
        "Shared Read Blocks": 0,
    },
    "Planning Time": 0.1,
    "Execution Time": 0.01,
}

INDEX_SCAN = {
    "Plan": {
        "Node Type": "Index Scan",
        "Relation Name": "users",
        "Alias": "users",
        "Index Name": "users_email_idx",
        "Startup Cost": 0.43,
        "Total Cost": 8.45,
        "Plan Rows": 1,
        "Plan Width": 80,
        "Actual Startup Time": 0.05,
        "Actual Total Time": 0.06,
        "Actual Rows": 1,
        "Actual Loops": 1,
        "Shared Hit Blocks": 4,
        "Shared Read Blocks": 0,
    },
    "Planning Time": 0.2,
    "Execution Time": 0.1,
}

HASH_JOIN_WITH_SEQ_SCAN = {
    "Plan": {
        "Node Type": "Hash Join",
        "Join Type": "Inner",
        "Startup Cost": 250.00,
        "Total Cost": 1800.00,
        "Plan Rows": 5000,
        "Plan Width": 120,
        "Actual Startup Time": 12.3,
        "Actual Total Time": 95.4,
        "Actual Rows": 4800,
        "Actual Loops": 1,
        "Shared Hit Blocks": 800,
        "Shared Read Blocks": 400,
        "Plans": [
            {
                "Node Type": "Seq Scan",
                "Relation Name": "orders",
                "Alias": "orders",
                "Startup Cost": 0.00,
                "Total Cost": 750.00,
                "Plan Rows": 50000,
                "Plan Width": 60,
                "Actual Startup Time": 0.01,
                "Actual Total Time": 28.3,
                "Actual Rows": 50000,
                "Actual Loops": 1,
                "Shared Hit Blocks": 400,
                "Shared Read Blocks": 200,
            },
            {
                "Node Type": "Hash",
                "Startup Cost": 100.00,
                "Total Cost": 100.00,
                "Plan Rows": 1000,
                "Plan Width": 60,
                "Actual Startup Time": 5.2,
                "Actual Total Time": 5.2,
                "Actual Rows": 1000,
                "Actual Loops": 1,
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Relation Name": "users",
                        "Alias": "users",
                        "Startup Cost": 0.00,
                        "Total Cost": 100.00,
                        "Plan Rows": 1000,
                        "Plan Width": 60,
                        "Actual Startup Time": 0.01,
                        "Actual Total Time": 4.8,
                        "Actual Rows": 1000,
                        "Actual Loops": 1,
                        "Shared Hit Blocks": 200,
                        "Shared Read Blocks": 100,
                    }
                ],
            },
        ],
    },
    "Planning Time": 1.2,
    "Execution Time": 96.0,
}

SORT_WITHOUT_INDEX = {
    "Plan": {
        "Node Type": "Sort",
        "Sort Key": ["created_at DESC"],
        "Startup Cost": 500.00,
        "Total Cost": 600.00,
        "Plan Rows": 10000,
        "Plan Width": 80,
        "Actual Startup Time": 22.1,
        "Actual Total Time": 25.4,
        "Actual Rows": 10000,
        "Actual Loops": 1,
        "Plans": [
            {
                "Node Type": "Seq Scan",
                "Relation Name": "events",
                "Alias": "events",
                "Startup Cost": 0.00,
                "Total Cost": 300.00,
                "Plan Rows": 10000,
                "Plan Width": 80,
                "Actual Startup Time": 0.01,
                "Actual Total Time": 12.3,
                "Actual Rows": 10000,
                "Actual Loops": 1,
            }
        ],
    },
    "Planning Time": 0.5,
    "Execution Time": 25.9,
}

NESTED_LOOP_LARGE = {
    "Plan": {
        "Node Type": "Nested Loop",
        "Join Type": "Inner",
        "Startup Cost": 0.43,
        "Total Cost": 9500.00,
        "Plan Rows": 500,
        "Plan Width": 100,
        "Actual Startup Time": 0.1,
        "Actual Total Time": 320.5,
        "Actual Rows": 500,
        "Actual Loops": 200,
        "Plans": [
            {
                "Node Type": "Seq Scan",
                "Relation Name": "subscriptions",
                "Alias": "subscriptions",
                "Startup Cost": 0.00,
                "Total Cost": 50.00,
                "Plan Rows": 200,
                "Plan Width": 40,
                "Actual Startup Time": 0.01,
                "Actual Total Time": 2.3,
                "Actual Rows": 200,
                "Actual Loops": 1,
            },
            {
                "Node Type": "Index Scan",
                "Relation Name": "orders",
                "Index Name": "orders_user_id_idx",
                "Startup Cost": 0.43,
                "Total Cost": 8.00,
                "Plan Rows": 3,
                "Plan Width": 60,
                "Actual Startup Time": 0.05,
                "Actual Total Time": 1.5,
                "Actual Rows": 3,
                "Actual Loops": 200,
            },
        ],
    },
    "Planning Time": 0.8,
    "Execution Time": 321.0,
}

POOR_ROW_ESTIMATE = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "events",
        "Alias": "events",
        "Startup Cost": 0.00,
        "Total Cost": 500.00,
        "Plan Rows": 10,
        "Plan Width": 80,
        "Actual Startup Time": 0.01,
        "Actual Total Time": 45.0,
        "Actual Rows": 5000,
        "Actual Loops": 1,
    },
    "Planning Time": 0.3,
    "Execution Time": 45.1,
}

NO_ANALYZE = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Alias": "users",
        "Startup Cost": 0.00,
        "Total Cost": 1540.00,
        "Plan Rows": 10000,
        "Plan Width": 80,
    },
    "Planning Time": 0.5,
}
