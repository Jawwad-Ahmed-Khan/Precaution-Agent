INSERT_TASK = """
    INSERT INTO tasks (
        event_id, task_label, description, task_type,
        required_quantity, priority, target_location,
        target_location_name, status, created_by_type,
        estimated_duration_hours, created_at, updated_at
    ) VALUES (
        $1, $2, $3, $4::task_type, $5, $6::task_priority,
        ST_MakePoint($7, $8)::geography,
        $9, 'unallocated', 'ai', $10, now(), now()
    )
    RETURNING task_id;
"""

INSERT_TASK_STATUS_HISTORY = """
    INSERT INTO task_status_history (
        task_id, old_status, new_status, change_reason, created_at
    ) VALUES (
        $1, NULL, 'unallocated',
        'Task created by Precaution Definer AI Agent',
        now()
    );
"""

GET_EXISTING_TASKS_FOR_EVENT = """
    SELECT task_id, task_label, task_type, status,
        priority, required_quantity, assigned_ngo_id
    FROM tasks
    WHERE event_id = $1 AND deleted_at IS NULL
    ORDER BY created_at ASC;
"""

GET_TASK_COUNT_FOR_EVENT = """
    SELECT COUNT(*) AS task_count
    FROM tasks
    WHERE event_id = $1 AND deleted_at IS NULL;
"""
