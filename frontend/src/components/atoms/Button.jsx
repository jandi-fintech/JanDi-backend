
export default function Button({ children, className = "", ...rest }) {
  return (
    <button
      className={`px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-semibold text-sm transition ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}