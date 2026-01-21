import { CSSProperties } from "react";
import HomePage from "./pages/HomePage";
import { colors } from "./theme/colors";

export default function App() {
  const themeStyle = {
    "--color-white": colors.white,
    "--color-black": colors.black,
    "--color-purple": colors.purple,
    "--color-blue": colors.blue,
    "--radius-base": "12px",
  } as CSSProperties;

  return (
    <div className="app-root" style={themeStyle}>
      <HomePage />
    </div>
  );
}
