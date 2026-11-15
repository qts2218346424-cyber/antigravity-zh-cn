import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Maximize2, Minimize2, Play, RotateCw, Swords } from 'lucide-react';
import '../../../resources/kimetsu_theater_engine.js';
import tanjiroImg from '../../../resources/media/tanjiro_water.webp';
import zenitsuImg from '../../../resources/media/zenitsu_thunder.webp';
import inosukeImg from '../../../resources/media/inosuke_beast.webp';
import nezukoImg from '../../../resources/media/nezuko_basket.webp';
import boxShockwaveImg from '../../../resources/media/box_impact_shockwave.webp';
import nezukoBoneHead from '../../../resources/media/nezuko_bone_head.webp';
import nezukoBoneTorso from '../../../resources/media/nezuko_bone_torso.webp';
import nezukoBoneArmL from '../../../resources/media/nezuko_bone_arm_l.webp';
import nezukoBoneArmR from '../../../resources/media/nezuko_bone_arm_r.webp';
import nezukoBoneLegL from '../../../resources/media/nezuko_bone_leg_l.webp';
import nezukoBoneLegR from '../../../resources/media/nezuko_bone_leg_r.webp';

interface DemonSlayerSplashPreviewProps {
  character: string;
}

const CHARACTER_SCRIPT_NOTES: Record<string, { badge: string; beats: string[] }> = {
  nezuko: {
    badge: '真实分肢骨骼飞踢 × 爆血火莲',
    beats: ['竹箱震裂冲破', '三连红爪空翻踢', '睁眼血鬼术爆血', '樱炎归护定格'],
  },
  tanjiro: {
    badge: '浮世绘水龙三连 × 日晕之龙炎斩',
    beats: ['静水呼吸白雾', '拾之型水龙螺旋', '火之神神乐圆舞', '赫刀收刃定格'],
  },
  zenitsu: {
    badge: '子弹时间居合 × 霹雳一闪六连瞬杀',
    beats: ['暴雨悬停低蹲', 'Z字六连金色雷闪', '火雷神斜贯劈空', '咔哒收刀归鞘'],
  },
  inosuke: {
    badge: '空间识觉声呐 × 双锯齿刃狂牙乱舞',
    beats: ['声呐脉冲锁定', '弹跳双刀连斩', 'X型狂牙撕裂破屏', '扛刀咆哮定格'],
  },
  all: {
    badge: '无限城四象联手 × 漫画斜切分镜合击',
    beats: ['炭治郎水龙前锋', '善逸三连雷闪切入', '伊之助+祢豆子协战', '四色螺旋爆炸 × 四分镜集结'],
  },
};

export const DemonSlayerSplashPreview: React.FC<DemonSlayerSplashPreviewProps> = ({ character }) => {
  const inlineStageRef = useRef<HTMLDivElement | null>(null);
  const modalStageRef = useRef<HTMLDivElement | null>(null);
  const instanceRef = useRef<{ replay: () => void; destroy: () => void } | null>(null);
  const modalInstanceRef = useRef<{ replay: () => void; destroy: () => void } | null>(null);
  const [fullscreen, setFullscreen] = useState(false);

  const assets = useMemo(
    () => ({
      tanjiro: tanjiroImg,
      zenitsu: zenitsuImg,
      inosuke: inosukeImg,
      nezuko: nezukoImg,
      box_impact_shockwave: boxShockwaveImg,
      nezuko_bone_head: nezukoBoneHead,
      nezuko_bone_torso: nezukoBoneTorso,
      nezuko_bone_arm_l: nezukoBoneArmL,
      nezuko_bone_arm_r: nezukoBoneArmR,
      nezuko_bone_leg_l: nezukoBoneLegL,
      nezuko_bone_leg_r: nezukoBoneLegR,
    }),
    [],
  );

  // 嵌入预览台挂载与切换角色热重载
  useEffect(() => {
    const el = inlineStageRef.current;
    if (!el || !window.KimetsuTheater) return;
    instanceRef.current?.destroy();
    instanceRef.current = window.KimetsuTheater.mount(el, {
      character,
      durationMs: 5600,
      loop: true,
      assets,
    });
    return () => {
      instanceRef.current?.destroy();
      instanceRef.current = null;
    };
  }, [character, assets]);

  // 全屏沉浸试看挂载
  useEffect(() => {
    if (!fullscreen) return;
    const el = modalStageRef.current;
    if (!el || !window.KimetsuTheater) return;
    modalInstanceRef.current?.destroy();
    modalInstanceRef.current = window.KimetsuTheater.mount(el, {
      character,
      durationMs: 5600,
      loop: true,
      assets,
    });
    return () => {
      modalInstanceRef.current?.destroy();
      modalInstanceRef.current = null;
    };
  }, [fullscreen, character, assets]);

  const note = CHARACTER_SCRIPT_NOTES[character] || CHARACTER_SCRIPT_NOTES.nezuko;

  return (
    <>
      <div className="rounded-xl border border-slate-700/70 bg-slate-950 overflow-hidden shadow-lg">
        {/* 顶栏操作条 */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-3.5 py-2 bg-slate-900/90 border-b border-slate-800 text-xs">
          <div className="flex items-center gap-2 text-slate-200 font-semibold">
            <Swords className="h-3.5 w-3.5 text-amber-400" />
            <span>实景战斗分镜预览</span>
            <span className="rounded-full bg-amber-500/15 border border-amber-400/30 px-2 py-0.5 text-[10.5px] font-medium text-amber-300">
              {note.badge}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => instanceRef.current?.replay()}
              className="inline-flex items-center gap-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1 text-[11px] font-medium transition-colors"
            >
              <RotateCw className="h-3 w-3" />
              重播连招
            </button>
            <button
              type="button"
              onClick={() => setFullscreen(true)}
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 text-[11px] font-medium transition-colors"
            >
              <Maximize2 className="h-3 w-3" />
              全屏影院试看
            </button>
          </div>
        </div>

        {/* 16:9 高燃 60fps 舞台 */}
        <div className="relative w-full aspect-[16/7.5] min-h-[240px] max-h-[340px] bg-black">
          <div ref={inlineStageRef} className="w-full h-full" />
        </div>

        {/* 招式分幕脚步条 */}
        <div className="flex flex-wrap items-center gap-1.5 px-3.5 py-2 bg-slate-900/80 border-t border-slate-800/90 text-[11px] text-slate-400">
          <Play className="h-3 w-3 text-emerald-400 mr-1" />
          <span>连招分幕：</span>
          {note.beats.map((b, idx) => (
            <React.Fragment key={b}>
              <span className="text-slate-200 font-medium">{b}</span>
              {idx < note.beats.length - 1 && <span className="text-slate-600">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 全屏试看浮层 */}
      {fullscreen && (
        <div className="fixed inset-0 z-50 bg-black/95 flex flex-col">
          <div className="flex items-center justify-between px-5 py-3 bg-slate-950/90 border-b border-slate-800">
            <div className="flex items-center gap-2 text-sm font-bold text-white">
              <Swords className="h-4 w-4 text-amber-400" />
              <span>Antigravity × 鬼灭之刃 · 全屏启动演出试看</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => modalInstanceRef.current?.replay()}
                className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 text-xs font-medium"
              >
                <RotateCw className="h-3.5 w-3.5" />
                重播本幕
              </button>
              <button
                type="button"
                onClick={() => setFullscreen(false)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white px-3 py-1.5 text-xs font-medium"
              >
                <Minimize2 className="h-3.5 w-3.5" />
                退出试看
              </button>
            </div>
          </div>
          <div className="flex-1 min-h-0 w-full">
            <div ref={modalStageRef} className="w-full h-full" />
          </div>
        </div>
      )}
    </>
  );
};
