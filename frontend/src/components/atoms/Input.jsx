export default function Input({ label, className = "", ...inputProps }) {
  return (
    <div className="flex flex-col text-sm">
      <label className="mb-1 font-medium text-gray-700 whitespace-nowrap">{label}</label>
      <input
        {...inputProps}
        className={`border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-indigo-200 ${className}`}
      />
    </div>
  );
}