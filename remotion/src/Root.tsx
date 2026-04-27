import React from "react";
import { Composition } from "remotion";
import { Play } from "./Play";
import type { Timing } from "./types";
import timingData from "../../script/timing.json";

const timing = timingData as unknown as Timing;

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
