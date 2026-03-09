import { Shell } from "./components/layout/Shell";
import { useAssets } from "./hooks/useAssets";

export default function App() {
  // Initialize asset loading on mount
  useAssets();
  return <Shell />;
}
