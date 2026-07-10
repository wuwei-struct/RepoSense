export function AdminButton(props: { user: any }) {
  const isAdmin = props.user?.role === "admin";
  return <button disabled={!isAdmin}>Rebuild admin cache</button>;
}

