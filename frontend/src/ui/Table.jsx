import React from 'react';

export default function Table({ columns, data, className = '' }) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-100">
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase"
              >
                {col.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-100">
          {data.map(row => (
            <tr key={row.id} className="hover:bg-slate-50 transition">
              {columns.map(col => (
                <td key={col.key} className="px-4 py-2 text-sm text-slate-700">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
