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

  const measures = ['top', 'bottom'].includes(dir) ? heights : widths;
  const positions = ['top', 'bottom'].includes(dir)
    ? verPositions
    : horPositions;
  const posLen = positions.length;
  const axis = ['top', 'bottom'].includes(dir) ? 'y' : 'x';
  const size = ['top', 'bottom'].includes(dir) ? 'height' : 'width';

  const windowStartEdge = windowFrame[axis];
  const windowEndEdge = windowStartEdge + windowFrame[size];

  for (let i = 0; i < posLen; i++) {
    if (['top', 'left'].includes(dir)) {
      // increase size to start
      let gridItemEdge = positions[posLen - 1 - i] + screenFrame[axis];
      if (windowStartEdge > screenFrame[axis]) {
        if (windowStartEdge <= gridItemEdge) continue;
        return window.setFrame({
          ...windowFrame,
          [axis]: gridItemEdge,
          [size]: windowFrame[size] + windowStartEdge - gridItemEdge,
        });
      }

      // decrease size from end
      gridItemEdge = gridItemEdge + measures[posLen - 1 - i];
      if (windowEndEdge <= gridItemEdge) continue;
      return window.setFrame({
        ...windowFrame,
        [size]: gridItemEdge - windowStartEdge,
      });
    }

    // increase size to end
    let gridItemEdge = positions[i] + measures[i] + screenFrame[axis];
    if (windowEndEdge < screenFrame[size] + screenFrame[axis]) {
      if (gridItemEdge <= windowEndEdge) continue;
      return window.setFrame({
        ...windowFrame,
        [size]: gridItemEdge - windowStartEdge,
      });
    }

    // decrease size from start
    gridItemEdge = gridItemEdge - measures[i];
    if (gridItemEdge <= windowStartEdge) continue;
    return window.setFrame({
      ...windowFrame,
      [axis]: gridItemEdge,
      [size]: windowFrame[size] + windowStartEdge - gridItemEdge,
    });
  }
}

function moveWindow(dir) {
  const focusedWindowInfo = getFocusedWindowInfo();

  if (!focusedWindowInfo) return;

  const { window, windowFrame, screenFrame } = focusedWindowInfo;
  const { horPositions, verPositions } = getGrid({
    sizeW: screenFrame.width,
    sizeH: screenFrame.height,
    hDivisions: HOR_DIVISIONS,
    vDivisions: VER_DIVISIONS,
    gapW: GAP_W,
    gapH: GAP_H,
  });

  const positions = ['top', 'bottom'].includes(dir)
    ? verPositions
    : horPositions;
  const posLen = positions.length;
  const axis = ['top', 'bottom'].includes(dir) ? 'y' : 'x';
  const windowStartEdge = windowFrame[axis];

  for (let i = 0; i < posLen; i++) {
    if (['top', 'left'].includes(dir)) {
      // move window to start
      const gridItemEdge = positions[posLen - 1 - i] + screenFrame[axis];
      if (windowStartEdge <= gridItemEdge) continue;
      return window.setFrame({ ...windowFrame, [axis]: gridItemEdge });
    }

    // move window to end
    const gridItemEdge = positions[i] + screenFrame[axis];
    if (windowStartEdge >= gridItemEdge) continue;
    return window.setFrame({ ...windowFrame, [axis]: gridItemEdge });
  }
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

Key.on('y', ['cmd', 'alt'], () => changeWindowSize('left'));
Key.on('o', ['cmd', 'alt'], () => changeWindowSize('right'));
Key.on('u', ['cmd', 'alt'], () => changeWindowSize('bottom'));
Key.on('i', ['cmd', 'alt'], () => changeWindowSize('top'));
Key.on('y', ['cmd', 'alt', 'shift'], () => moveWindow('left'));
Key.on('o', ['cmd', 'alt', 'shift'], () => moveWindow('right'));
Key.on('i', ['cmd', 'alt', 'shift'], () => moveWindow('top'));
Key.on('u', ['cmd', 'alt', 'shift'], () => moveWindow('bottom'));

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
