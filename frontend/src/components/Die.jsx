const PIP_POSITIONS = {
  1: [4],
  2: [2, 6],
  3: [2, 4, 6],
  4: [0, 2, 6, 8],
  5: [0, 2, 4, 6, 8],
  6: [0, 2, 3, 5, 6, 8],
};

export default function Die({ value, hidden, held, onClick, size = "w-9 h-9" }) {
  return (
    <button
      type="button"
      disabled={!onClick}
      onClick={onClick}
      className={`die-face ${size} p-1.5 ${held ? "ring-4 ring-chip-red" : ""} ${
        onClick ? "cursor-pointer" : "cursor-default"
      }`}
    >
      {hidden ? (
        <span className="w-full h-full flex items-center justify-center text-lg font-bold">?</span>
      ) : (
        <span className="grid grid-cols-3 grid-rows-3 w-full h-full">
          {Array.from({ length: 9 }).map((_, i) => (
            <span key={i} className="flex items-center justify-center">
              {(PIP_POSITIONS[value] || []).includes(i) && (
                <span className="w-[22%] h-[22%] rounded-full bg-[#1a1a1a]" />
              )}
            </span>
          ))}
        </span>
      )}
    </button>
  );
}
