import { Config } from "@remotion/cli/config";

// 레포 루트를 public 디렉토리로 설정해서
// staticFile("voices/...mp3"), staticFile("images/scene_X.png") 식으로
// 접근할 수 있게 한다. 로컬 렌더링 전용이므로 노출 우려 없음.
Config.setPublicDir("../");

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// 기본 concurrency를 2로 제한 — 자막/이미지/오디오가 한 프레임에 같이
// 올라가는 합성이라 코어 수만큼 띄우면 크롬이 OOM으로 죽는다.
// CLI에서 --concurrency=N 으로 덮어쓸 수 있다.
Config.setConcurrency(2);
