const HOR_DIVISIONS = 12;
const VER_DIVISIONS = 12;
const GAP_W = 0;
const GAP_H = 0;

function getDimensionMeasures(size, divisions, gap = 0) {
  const measures = [];
  const positions = [];
  const sizeWithoutGaps = size - (gap > 0 ? (divisions - 1) * gap : 0);

  const itemSize = Math.floor(sizeWithoutGaps / divisions);

  let remainder = sizeWithoutGaps % divisions;
  const initPosForItemsWith1PixelMore =
    Math.floor(divisions / 2) - Math.floor(remainder / 2);

  let total = 0;
  for (let i = 0; i < divisions; i++) {
    measures[i] = itemSize;

    if (i >= initPosForItemsWith1PixelMore && remainder > 0) {
      measures[i] = itemSize + 1;
      remainder = remainder - 1;
    }

    positions[i] = total;
    total = total + measures[i] + gap;
  }

  return { measures, positions };
}

function getGrid({ sizeW, sizeH, hDivisions, vDivisions, gapW, gapH }) {
  const { measures: widths, positions: horPositions } = getDimensionMeasures(
    sizeW,
    hDivisions,
    gapW
  );

  const { measures: heights, positions: verPositions } = getDimensionMeasures(
    sizeH,
    vDivisions,
    gapH
  );

  return { widths, horPositions, heights, verPositions };
}

function showModal(msg, duration = 1) {
  const modal = new Modal();
  modal.message = JSON.stringify(msg);
  modal.duration = duration;
  modal.show();
}

function getFocusedWindowInfo() {
  const window = Window.focused();
  const windowFrame = window?.frame?.();
  const screen = window?.screen?.();
  const screenFrame = screen?.flippedVisibleFrame?.();

  if (!windowFrame || !screenFrame) return null;

  return { window, windowFrame, screen, screenFrame };
}

function getWindowStartEdges({ positions, windowStartEdge, screenStartEdge }) {
  const posLen = positions.length;
  let curWindowStartEdge = positions[0];
  let prevWindowStartEdge = curWindowStartEdge;
  let nextWindowStartEdge = curWindowStartEdge;

  for (let i = 0; i < posLen; i++) {
    const startEdge = screenStartEdge + positions[i];

    if (startEdge > windowStartEdge) break;

    curWindowStartEdge = startEdge;
    prevWindowStartEdge =
      i > 0 ? screenStartEdge + positions[i - 1] : startEdge;
    nextWindowStartEdge =
      i < posLen - 1 ? screenStartEdge + positions[i + 1] : startEdge;
  }

  return { curWindowStartEdge, prevWindowStartEdge, nextWindowStartEdge };
}

function getWindowEndEdges({
  positions,
  measures,
  windowEndEdge,
  screenStartEdge,
}) {
  const posLen = positions.length;
  let curWindowEndEdge = positions[posLen - 1] + measures[posLen - 1];
  let prevWindowEndEdge = curWindowEndEdge;
  let nextWindowEndEdge = curWindowEndEdge;

  for (let i = 0; i < posLen; i++) {
    const endEdge = screenStartEdge + positions[i] + measures[i];

    if (endEdge < windowEndEdge) continue;

    curWindowEndEdge = endEdge;
    prevWindowEndEdge =
      i > 0 ? screenStartEdge + positions[i - 1] + measures[i - 1] : endEdge;
    nextWindowEndEdge =
      i < posLen - 1
        ? screenStartEdge + positions[i + 1] + measures[i + 1]
        : endEdge;

    break;
  }

  return { curWindowEndEdge, prevWindowEndEdge, nextWindowEndEdge };
}

function forceWindowInGrid({
  onlyMove,
  dir,
  windowStartEdge,
  windowEndEdge,
  screenEndEdge,

  axis,
  size,
  window,
  windowFrame,
  positions,
  measures,
  screenStartEdge,
  newWindowStartEdge,
  newWindowEndEdge,
}) {
  if (
    onlyMove &&
    ((dir === 'prev' && windowStartEdge === screenStartEdge) ||
      (dir === 'next' && windowEndEdge === screenEndEdge)) &&
    windowFrame[axis] === windowStartEdge &&
    windowFrame[size] === windowEndEdge - windowStartEdge
  )
    return;

  // try to resize and move window with given args within grid
  const newSize = newWindowEndEdge - newWindowStartEdge;

  window.setFrame({
    ...windowFrame,
    [size]: newSize,
    [axis]: newWindowStartEdge,
  });

  if (window.frame()[size] <= newSize) return;

  // if it does not fit correctly in grid...
  // try to increase size towards end
  const posLen = positions.length;

  for (let j = 0; j < posLen; j++) {
    const tmpWindowEndEdge = screenStartEdge + positions[j] + measures[j];
    if (tmpWindowEndEdge <= newWindowEndEdge) continue;

    const newSize = tmpWindowEndEdge - newWindowStartEdge;

    window.setFrame({
      ...windowFrame,
      [axis]: newWindowStartEdge,
      [size]: newSize,
    });

    if (window.frame()[size] <= newSize) return true;
  }

  // try to increase size towards start
  for (let j = posLen - 1; j >= 0; j--) {
    const tmpWindowStartEdge = screenStartEdge + positions[j];
    if (tmpWindowStartEdge > newWindowStartEdge) continue;

    const newSize = newWindowEndEdge - tmpWindowStartEdge;

    window.setFrame({
      ...windowFrame,
      [axis]: tmpWindowStartEdge,
      [size]: newSize,
    });

    if (window.frame()[size] <= newSize) return;
  }

  showModal('Could not force the window in Grid');
  throw new Error('Could not force the window in Grid');
}

function changeWindowSize(dir) {
  const focusedWindowInfo = getFocusedWindowInfo();

  if (!focusedWindowInfo) return;

  const { window, windowFrame, screenFrame } = focusedWindowInfo;
  const { widths, heights, horPositions, verPositions } = getGrid({
    sizeW: screenFrame.width,
    sizeH: screenFrame.height,
    hDivisions: HOR_DIVISIONS,
    vDivisions: VER_DIVISIONS,
    gapW: GAP_W,
    gapH: GAP_H,
  });

  const isVerAxis = ['top', 'bottom', 'moveTop', 'moveBottom'].includes(dir);
  const measures = isVerAxis ? heights : widths;
  const positions = isVerAxis ? verPositions : horPositions;
  const axis = isVerAxis ? 'y' : 'x';
  const size = isVerAxis ? 'height' : 'width';

  const windowStartEdge = windowFrame[axis];
  const windowEndEdge = windowStartEdge + windowFrame[size];
  const screenStartEdge = screenFrame[axis];
  const screenEndEdge = screenStartEdge + screenFrame[size];

  const { curWindowStartEdge, prevWindowStartEdge, nextWindowStartEdge } =
    getWindowStartEdges({
      positions,
      measures,
      windowStartEdge,
      screenStartEdge,
    });

  const { curWindowEndEdge, prevWindowEndEdge, nextWindowEndEdge } =
    getWindowEndEdges({
      positions,
      measures,
      windowEndEdge,
      screenStartEdge,
    });

  if (['top', 'left'].includes(dir))
    return forceWindowInGrid({
      axis,
      size,
      window,
      windowFrame,
      measures,
      positions,
      screenStartEdge,
      newWindowStartEdge: curWindowStartEdge,
      newWindowEndEdge: prevWindowEndEdge,
    });

  if (['bottom', 'right'].includes(dir))
    return forceWindowInGrid({
      axis,
      size,
      window,
      windowFrame,
      measures,
      positions,
      screenStartEdge,
      newWindowStartEdge: curWindowStartEdge,
      newWindowEndEdge: nextWindowEndEdge,
    });

  if (
    ((dir === 'prev' && windowStartEdge === screenStartEdge) ||
      (dir === 'next' && curWindowEndEdge === screenEndEdge)) &&
    windowFrame[axis] === windowStartEdge &&
    windowFrame[size] === windowEndEdge - windowStartEdge
  )
    return;

  if (['moveTop', 'moveLeft'].includes(dir))
    return forceWindowInGrid({
      onlyMove: true,
      dir: 'prev',
      windowStartEdge,
      windowEndEdge,

      axis,
      size,
      window,
      windowFrame,
      measures,
      positions,
      screenStartEdge,
      newWindowStartEdge: prevWindowStartEdge,
      newWindowEndEdge: prevWindowEndEdge,
    });

  if (['moveBottom', 'moveRight'].includes(dir))
    return forceWindowInGrid({
      onlyMove: true,
      dir: 'next',
      windowEndEdge,
      windowStartEdge,
      screenEndEdge,

      axis,
      size,
      window,
      windowFrame,
      measures,
      positions,
      screenStartEdge,
      newWindowStartEdge: nextWindowStartEdge,
      newWindowEndEdge: nextWindowEndEdge,
    });
}

function set4x4WindowFrame(newWinKey, direction, newWinMaps) {
  const focusedWindowInfo = getFocusedWindowInfo();
  if (!focusedWindowInfo) return;

  const { window, windowFrame, screenFrame } = focusedWindowInfo;
  const { widths, heights } = getGrid({
    sizeW: screenFrame.width,
    sizeH: screenFrame.height,
    hDivisions: 2,
    vDivisions: 2,
  });

  const [halfWidthLeft, halfWidthRight] = widths;
  const [halfHeightTop, halfHeightBottom] = heights;

  const grid4x4 = {
    maximized: {
      x: screenFrame.x,
      y: screenFrame.y,
      width: screenFrame.width,
      height: screenFrame.height,
    },
    halfLeft: {
      x: screenFrame.x,
      y: screenFrame.y,
      width: halfWidthLeft,
      height: screenFrame.height,
    },
    topHalfLeft: {
      x: screenFrame.x,
      y: screenFrame.y,
      width: halfWidthLeft,
      height: halfHeightTop,
    },
    bottomHalfLeft: {
      x: screenFrame.x,
      y: screenFrame.y + halfHeightTop,
      width: halfWidthLeft,
      height: halfHeightBottom,
    },
    halfRight: {
      x: screenFrame.x + halfWidthLeft,
      y: screenFrame.y,
      width: halfWidthRight,
      height: screenFrame.height,
    },
    topHalfRight: {
      x: screenFrame.x + halfWidthLeft,
      y: screenFrame.y,
      width: halfWidthRight,
      height: halfHeightTop,
    },
    bottomHalfRight: {
      x: screenFrame.x + halfWidthLeft,
      y: screenFrame.y + halfHeightTop,
      width: halfWidthRight,
      height: halfHeightBottom,
    },
  };

  if (!newWinMaps) {
    newWinMaps = {
      maximized: 'halfLeft',
      halfLeft: 'halfRight',
      halfRight: 'topHalfLeft',
      topHalfLeft: 'bottomHalfLeft',
      bottomHalfLeft: 'topHalfRight',
      topHalfRight: 'bottomHalfRight',
      bottomHalfRight: 'maximized',
    };
  }

  if (direction) {
    const key = Object.keys(grid4x4).find((key) => {
      const gridEl = grid4x4[key];

      return (
        gridEl.x === windowFrame.x &&
        gridEl.y === windowFrame.y &&
        // theres a glitch where the height is not set properly
        // and it is off by 1 pixel
        Math.abs(gridEl.width - windowFrame.width) <= 1 &&
        Math.abs(gridEl.height - windowFrame.height) <= 1
      );
    });

    if (direction === 'next') {
      newWinKey = newWinMaps[key] ? newWinMaps[key] : newWinKey;
    } else {
      newWinKey = newWinMaps[key]
        ? Object.keys(newWinMaps).find((key2) => newWinMaps[key2] === key)
        : newWinKey;
    }
  }

  window.setFrame(grid4x4[newWinKey]);
}

Key.on('k', ['cmd', 'alt'], () => set4x4WindowFrame('maximized'));

Key.on('h', ['cmd', 'alt'], () =>
  set4x4WindowFrame('halfLeft', 'next', {
    halfLeft: 'topHalfLeft',
    topHalfLeft: 'bottomHalfLeft',
    bottomHalfLeft: 'halfLeft',
  })
);

Key.on('l', ['cmd', 'alt'], () =>
  set4x4WindowFrame('halfRight', 'next', {
    halfRight: 'topHalfRight',
    topHalfRight: 'bottomHalfRight',
    bottomHalfRight: 'halfRight',
  })
);

Key.on('h', ['ctrl'], () => changeWindowSize('moveLeft'));
Key.on('h', ['ctrl', 'shift'], () => changeWindowSize('left'));
Key.on('l', ['ctrl'], () => changeWindowSize('moveRight'));
Key.on('l', ['ctrl', 'shift'], () => changeWindowSize('right'));
Key.on('j', ['ctrl'], () => changeWindowSize('moveBottom'));
Key.on('j', ['ctrl', 'shift'], () => changeWindowSize('bottom'));
Key.on('k', ['ctrl'], () => changeWindowSize('moveTop'));
Key.on('k', ['ctrl', 'shift'], () => changeWindowSize('top'));

////////////////////////////////////
///////////// TESTS ////////////////
////////////////////////////////////

(() => {
  let allTestsPassed = true;

  function expectDeepEqual(input, expected) {
    if (JSON.stringify(input) === JSON.stringify(expected)) return;
    allTestsPassed = false;
  }

  expectDeepEqual(
    getGrid({ sizeW: 27, sizeH: 26, hDivisions: 5, vDivisions: 5 }),
    {
      widths: [5, 6, 6, 5, 5],
      horPositions: [0, 5, 11, 17, 22],
      heights: [5, 5, 6, 5, 5],
      verPositions: [0, 5, 10, 16, 21],
    }
  );
  expectDeepEqual(
    getGrid({ sizeW: 10, sizeH: 28, hDivisions: 2, vDivisions: 5 }),
    {
      widths: [5, 5],
      horPositions: [0, 5],
      heights: [5, 6, 6, 6, 5],
      verPositions: [0, 5, 11, 17, 23],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 27,
      sizeH: 26,
      hDivisions: 5,
      vDivisions: 5,
      gapW: 2,
      gapH: 2,
    }),
    {
      widths: [4, 4, 4, 4, 3],
      horPositions: [0, 6, 12, 18, 24],
      heights: [3, 4, 4, 4, 3],
      verPositions: [0, 5, 11, 17, 23],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 27,
      sizeH: 26,
      hDivisions: 5,
      vDivisions: 5,
      gapW: 3,
      gapH: 3,
    }),
    {
      widths: [3, 3, 3, 3, 3],
      horPositions: [0, 6, 12, 18, 24],
      heights: [3, 3, 3, 3, 2],
      verPositions: [0, 6, 12, 18, 24],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 27,
      sizeH: 26,
      hDivisions: 5,
      vDivisions: 5,
      gapW: 4,
      gapH: 4,
    }),
    {
      widths: [2, 2, 3, 2, 2],
      horPositions: [0, 6, 12, 19, 25],
      heights: [2, 2, 2, 2, 2],
      verPositions: [0, 6, 12, 18, 24],
    }
  );

  expectDeepEqual(
    getGrid({
      sizeW: 10,
      sizeH: 28,
      hDivisions: 2,
      vDivisions: 5,
      gapW: 1,
      gapH: 1,
    }),
    {
      widths: [4, 5],
      horPositions: [0, 5],
      heights: [5, 5, 5, 5, 4],
      verPositions: [0, 6, 12, 18, 24],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 10,
      sizeH: 28,
      hDivisions: 2,
      vDivisions: 5,
      gapW: 2,
      gapH: 2,
    }),
    {
      widths: [4, 4],
      horPositions: [0, 6],
      heights: [4, 4, 4, 4, 4],
      verPositions: [0, 6, 12, 18, 24],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 10,
      sizeH: 28,
      hDivisions: 2,
      vDivisions: 5,
      gapW: 3,
      gapH: 3,
    }),
    {
      widths: [3, 4],
      horPositions: [0, 6],
      heights: [3, 3, 4, 3, 3],
      verPositions: [0, 6, 12, 19, 25],
    }
  );
  expectDeepEqual(
    getGrid({
      sizeW: 10,
      sizeH: 28,
      hDivisions: 2,
      vDivisions: 5,
      gapW: 4,
      gapH: 4,
    }),
    {
      widths: [3, 3],
      horPositions: [0, 7],
      heights: [2, 3, 3, 2, 2],
      verPositions: [0, 6, 13, 20, 26],
    }
  );

  if (!allTestsPassed) {
    showModal('A Test failed', 5);
    throw 'A Test failed';
  }
})();
