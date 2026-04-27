import React from "react";
import { Composition } from "remotion";
import { Play } from "./Play";
import timing from "../../script/timing.json";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Play"
        component={Play}
        durationInFrames={Math.max(1, timing.total_duration_frames)}
        fps={timing.fps}
        width={timing.width}
        height={timing.height}
      />
    </>
  );
};
