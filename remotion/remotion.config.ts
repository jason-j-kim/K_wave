import { Config } from "@remotion/cli/config";

// 레포 루트를 public 디렉토리로 설정해서
// staticFile("voices/...mp3"), staticFile("images/scene_X.png") 식으로
// 접근할 수 있게 한다. 로컬 렌더링 전용이므로 노출 우려 없음.
Config.setPublicDir("../");

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
