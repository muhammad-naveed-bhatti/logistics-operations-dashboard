# Role & Permission Matrix

This portfolio demo uses a role selector to simulate access. The selector is not a security boundary. When Supabase Auth is introduced, the same role model should be enforced with Auth + Row Level Security (RLS).

| Role | Main visibility | Write/action authority |
|---|---|---|
| Senior Officers | Executive, fleet, materials, dispatch, finance, maintenance, gate movement | Oversight/read-only in demo |
| Log Staff Supervisor | Operations, materials, dispatch, maintenance, gate movement | Supervisory oversight |
| Log Staff | Fleet, materials, dispatch | Routine logistics work |
| Motor Vehicle Operations | Fleet, dispatch, gate passes | Generate soft gate passes |
| Fleet Drivers | Own vehicle/task and own gate pass | No cross-driver access |
| Accountant | Finance panel | Finance workflow only |
| Motor Vehicle Maintenance | Maintenance jobs and fleet view | Update maintenance job status |
| Gate Security | Active gate passes and movement log | Record vehicle IN / OUT only |

## Gate-pass workflow
1. Motor Vehicle Operations selects the vehicle/task and generates a soft gate pass.
2. The assigned driver can see only their own assignment and pass in the driver panel.
3. Gate Security validates the active pass.
4. Gate Security records vehicle OUT.
5. On return, Gate Security records vehicle IN and the pass is closed.
6. Senior Officers / Log Staff Supervisor can review movement history but cannot impersonate the gate-security action in the demo.

## Production security direction
Authorization data should be stored in Supabase Auth `app_metadata`, not user-editable metadata. Public-schema tables must use RLS. UI hiding alone is not sufficient security.
