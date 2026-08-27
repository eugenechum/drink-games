const PIP_POSITIONS = {
  1: [4],
  2: [2, 6],
  3: [2, 4, 6],
  4: [0, 2, 6, 8],
  5: [0, 2, 4, 6, 8],
  6: [0, 2, 3, 5, 6, 8],
};

const DOT_SIZE = {
  "w-9 h-9": "w-3 h-3",
  "w-11 h-11": "w-3.5 h-3.5",
  "w-12 h-12": "w-3.5 h-3.5",
  "w-14 h-14": "w-4 h-4",
  "w-16 h-16": "w-5 h-5",
};

export default function Die({ value, hidden, held, onClick, size = "w-9 h-9" }) {
  const dot = DOT_SIZE[size] || "w-3 h-3";
  return (
    <button
      type="button"
      disabled={!onClick}
      onClick={onClick}
      className={`die-face relative ${size} ${onClick ? "cursor-pointer" : "cursor-default"}`}
      style={
        held
          ? { backgroundColor: "rgba(179, 18, 44, 0.3)", boxShadow: "0 0 0 4px #b3122c" }
          : undefined
      }
    >
      {hidden ? (
        <span className="absolute inset-0 flex items-center justify-center text-lg font-bold">?</span>
      ) : (
        <span className="absolute inset-0 grid grid-cols-3 grid-rows-3 place-items-center p-1">
          {Array.from({ length: 9 }).map((_, i) =>
            (PIP_POSITIONS[value] || []).includes(i) ? (
              <span key={i} className={`${dot} rounded-full bg-[#1a1a1a]`} />
            ) : (
              <span key={i} />
            )
          )}
        </span>
      )}
      {held && (
        <span className="absolute -top-2 -right-2 bg-chip-red text-white text-[11px] font-bold rounded-full w-5 h-5 flex items-center justify-center shadow">
          ✓
        </span>
      )}
    </button>
  );
}
