<template>
  <div>
    <div class="stat time">
      Секунд прошло: {{ startTime }}
    </div>

    <div class="stat epoch">
      Шаг: {{ actor.step }} | Эпох: {{ epoch }} | Побед: {{ win }}
    </div>

    <div
      ref="Square"
      class="Square"
      tabindex="0"
      @keyup.up="handJumpTop"
      @keyup.right="handJumpRight"
      @keyup.down="handJumpBottom"
      @keyup.left="handJumpLeft"
    >
      <div class="cells field">
        <div
          v-for="(cellValue, index) in field"
          :key="index"
          :class="['cell', { 'available': cellValue === 2 }]"
        >
          <div
            v-if="cellValue === 1"
            class="starting-checkpoint"
          >
            СТАРТ
          </div>

          <div
            v-if="cellValue === 3"
            class="middle-checkpoint"
          >
            БЕГИ
          </div>

          <div
            v-if="cellValue === 4"
            class="finishing-checkpoint"
          >
            ФИНИШ
          </div>
        </div>
      </div>

      <div class="players field">
        <div class="player">
          <div class="actor">
            🐥
          </div>

          <!-- Усики сканирующие, что там дальше. -->
          <div class="antenna jump-top" />
          <div class="antenna jump-right" />
          <div class="antenna jump-bottom" />
          <div class="antenna jump-left" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';

// function getRandomArbitrary([min, max]) {
//   return Math.random() * (max - min) + min;
// }

const automaticControl = true;

// Максимальное значение ячейки.
const maxCellValues = 4;
// Минимальное количество ходов для выигрыша.
const maxStep = 32; // 8

const field = [
  0, 0, 0, 0, 0, 0, 0,
  0, 1, 0, 0, 0, 0, 0,
  0, 2, 0, 0, 0, 0, 0,
  0, 2, 0, 0, 0, 0, 0,
  0, 2, 0, 0, 0, 0, 0,
  0, 3, 2, 2, 2, 4, 0,
  0, 0, 0, 0, 0, 0, 0,
];

export default {
  name: 'Square',

  data() {
    return {
      time: Date(),
      startTime: 0,
      style: undefined,

      // Игровая область обязательно квадратной формы.
      // 0 - Запретная территория.
      // 1 - Проходная территория.
      // 2 - Начальная точка.
      // 3 - Промежуточная точка.
      // 4 - Финишная точка.
      field,
      size: -1,
      quantityColumns: -1,
      quantityRows: -1,

      actor: {
        x: 2,
        y: 2,
        step: 0,
        cellValueTop: 0,
        cellValueRight: 0,
        cellValueBottom: 0,
        cellValueLeft: 0,
      },
      actorDelay: 1000,

      model: tf.sequential(),
      epoch: 0,
      win: 0,
      training: {
        // [x, y, step] - Нормализованные координаты актёра.
        // step - количество шагов, сделанных со стартовой позиции.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },
    };
  },

  async mounted() {
    this.setupModel();

    // Timer.
    setInterval(() => {
      this.time = Date();
      this.startTime += 1;
    }, 1000);

    this.style = this.$refs.Square.style;

    this.settingPlayingField();

    await this.setPlayerStyleProperties();

    if (automaticControl) {
      await this.modelPredict();
    }

    this.checkExit();
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        // [
        //   x, y, // Нормализованные координаты актёра.
        //   step, // Количество шагов, сделанных от стартовой позиции.
        //   4 усика // Направлены во все 4 стороны от актёра.
        // ]
        inputShape: [3 + 4],
        activation: 'sigmoid',
        units: 32,
      }));

      // this.model.add(tf.layers.dense({
      //   inputShape: [32],
      //   activation: 'sigmoid',
      //   units: 32,
      // }));

      this.model.add(tf.layers.dense({
        inputShape: [32],
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
      });
    },

    settingPlayingField() {
      this.size = Math.sqrt(this.field.length);
      this.quantityColumns = this.size;
      this.quantityRows = this.size;

      this.style.setProperty('--quantity-columns', this.quantityColumns);
      this.style.setProperty('--quantity-rows', this.quantityRows);
    },

    async setPlayerStyleProperties() {
      const { x, y } = this.actor;

      this.style.setProperty('--player-column', x);
      this.style.setProperty('--player-row', y);

      if (this.actor.step === maxStep) {
        await this.modelFit();
      }
    },

    async checkExit() {
      const { x, y } = this.actor;
      // Смещение на -1: Сетка начинается с 1, а значения в массиве начинаются с 0.
      const normalY = y - 1;
      const normalX = x - 1;

      const cellValue = this.field[normalY * this.size + normalX];
      // this.field[normalY * this.size + normalX] = 0;

      // Очень важно передавать значения в label[] в таком же порядке!
      const [
        cellValueTop,
        cellValueRight,
        cellValueBottom,
        cellValueLeft,
      ] = this.getAntennaCellValues({ normalX, normalY });

      this.actor = {
        ...this.actor,
        cellValueTop,
        cellValueRight,
        cellValueBottom,
        cellValueLeft,
      };

      const label = [
        cellValueTop,
        cellValueRight,
        cellValueBottom,
        cellValueLeft,
      ];

      // Тренировать на накопленных training.inputs при выходе за границы.
      let isModelFit = false;

      switch (cellValue) {
        case 0:
          isModelFit = true;
          break;

        case 1:
          break;

        case 2:
        case 3:
          this.actor.step += 1;
          break;

        case 4:
          isModelFit = true;
          console.log('ФИНИШ!', x, y);

          this.actor.step += 1;
          this.win += 1;
          break;

        default:
          console.log('Опс!');
      }

      if (!automaticControl) {
        // Для проверки, куда актёр пришёл.
        console.log(`x: ${x} | y: ${y} | step: ${this.actor.step} | cellValue: ${cellValue} | label: ${label}`);
        console.log(cellValueTop, cellValueRight, cellValueBottom, cellValueLeft);
      }

      this.training.inputs.push([
        x / this.size,
        y / this.size,
        this.actor.step / maxStep,
        cellValueTop / maxCellValues,
        cellValueRight / maxCellValues,
        cellValueBottom / maxCellValues,
        cellValueLeft / maxCellValues,
      ]);

      this.training.labels.push(label);

      if (isModelFit) {
        await this.modelFit();
      }

      if (automaticControl) {
        await this.modelPredict();
      }
    },

    // Получение значения ячейки от 1 до 4.
    getAntennaCellValues({ normalX, normalY }) {
      // || 0 - когда выходит на запретную зону, то дальше нет пути, считаем, что тоже запретная.
      const top = this.field[(normalY - 1) * this.size + normalX] || 0;
      const right = this.field[normalY * this.size + (normalX + 1)] || 0;
      const bottom = this.field[(normalY + 1) * this.size + normalX] || 0;
      const left = this.field[normalY * this.size + (normalX - 1)] || 0;

      return [top, right, bottom, left];
    },

    // Возвращает 2 значения, для вычисления случайного числа между ними.
    checkCellValue(cellValue) {
      // Означает, что в ячейку можно наступить.
      if (cellValue > 0) {
        return [0.4, 0.6];
      }

      return [0, 0];
    },

    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      await this.resetGame();
    },

    async resetGame() {
      this.epoch += 1;

      this.actor = {
        ...this.actor,
        x: 2,
        y: 2,
        step: 0,
        cellValueTop: 0,
        cellValueRight: 0,
        cellValueBottom: 0,
        cellValueLeft: 0,
      };

      // this.field = JSON.parse(JSON.stringify(field));

      await this.setPlayerStyleProperties();

      if (automaticControl) {
        await this.modelPredict();
      }

      this.checkExit();
    },

    async modelPredict() {
      const {
        x,
        y,
        step,
        cellValueTop,
        cellValueRight,
        cellValueBottom,
        cellValueLeft,
      } = this.actor;

      const prediction = this.model.predict(tf.tensor2d([
        [
          x / this.size,
          y / this.size,
          step / maxStep,
          cellValueTop / maxCellValues,
          cellValueRight / maxCellValues,
          cellValueBottom / maxCellValues,
          cellValueLeft / maxCellValues,
        ],
      ]));

      const [jumpTop, jumpRight, jumpBottom, jumpLeft] = await prediction.data();
      console.log(
        'Top', jumpTop.toFixed(4),
        'Right', jumpRight.toFixed(4),
        'Bottom', jumpBottom.toFixed(4),
        'Left', jumpLeft.toFixed(4),
      );

      let maximum = jumpTop;
      let action = 'jumpTop';

      if (jumpRight > maximum) {
        maximum = jumpRight;
        action = 'jumpRight';
      }

      if (jumpBottom > maximum) {
        maximum = jumpBottom;
        action = 'jumpBottom';
      }

      if (jumpLeft > maximum) {
        maximum = jumpLeft;
        action = 'jumpLeft';
      }

      this[action]();

      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    jumpTop() {
      this.actor.y -= 1;
    },

    jumpRight() {
      this.actor.x += 1;
    },

    jumpBottom() {
      this.actor.y += 1;
    },

    jumpLeft() {
      this.actor.x -= 1;
    },

    // Специально для ручного управления.
    async handJumpTop() {
      this.jumpTop();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpRight() {
      this.jumpRight();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpBottom() {
      this.jumpBottom();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpLeft() {
      this.jumpLeft();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },
  },
};
</script>

<style
  lang='scss'
  scoped
>
.Square {
  --quantity-rows: -1;
  --quantity-columns: -1;
  --column-width: 5rem;

  --player-row: -1;
  --player-column: -1;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;
  user-select: none;
}

.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.time {
  margin-top: 5rem;
  width: 100%;
  text-align: center;
}

.epoch {
  margin-top: 7rem;
  width: 100%;
  text-align: center;
}

.cells {
  .cell {
    display: flex;
    background-color: #222;
  }

  .available {
    background-color: darkcyan;
  }

  .starting-checkpoint,
  .middle-checkpoint,
  .finishing-checkpoint {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
    line-height: 0.9;
    font-weight: bold;
    background-color: seagreen;
    outline: 0.5rem dashed seagreen;
  }

  .middle-checkpoint {
    line-height: 1;
    color: green;
    background-color: greenyellow;
    outline: 0.5rem dashed greenyellow;
  }
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--column-width));
  grid-template-columns: repeat(var(--quantity-columns), var(--column-width));
  grid-gap: 1rem;
}

.players {
  position: absolute;

  .player {
    position: relative;
    grid-row: var(--player-row);
    grid-column: var(--player-column);
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: yellow;
    outline: 0.5rem dashed yellow;

    .actor {
      font-size: 2.4rem;
    }

    .antenna {
      position: absolute;
      height: 2px;
      width: 3rem;
      background-color: white;
    }

    .jump-top {
      top: -2rem;
      transform: rotate(90deg);
    }

    .jump-right {
      right: -3.5rem;
      transform: rotate(180deg);
    }

    .jump-bottom {
      bottom: -2rem;
      transform: rotate(270deg);
    }

    .jump-left {
      left: -3.5rem;
    }
  }
}
</style>
