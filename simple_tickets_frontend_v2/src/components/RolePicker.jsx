export default function RolePicker({ roles, selected = [], onChange, disabled = false }) {
  const set = new Set(selected || []);
  function toggle(id) {
    const next = new Set(set);
    if (next.has(id)) next.delete(id); else next.add(id);
    onChange?.([...next]);
  }
  return (
    <div className="role-picker">
      {roles.map((role) => (
        <label key={role.role_id} className="check-row">
          <input type="checkbox" disabled={disabled} checked={set.has(role.role_id)} onChange={() => toggle(role.role_id)} />
          <span>{role.name}</span>
          <small>#{role.role_id}</small>
        </label>
      ))}
      {!roles.length && <span className="muted">Роли не загружены</span>}
    </div>
  );
}
