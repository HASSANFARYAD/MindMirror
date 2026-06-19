declare module "canvas-confetti" {
  type Options = {
    particleCount?: number;
    spread?: number;
    colors?: string[];
    origin?: { x?: number; y?: number };
  };

  function confetti(options?: Options): void;

  export default confetti;
}
