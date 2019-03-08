<template>
  <a-scene
    id="Maze"
    physics="debug: false"
    stats="false"
    vr-mode-ui="enabled: false"
  >
    <a-assets id="AssetsImages">
      <img
        id="AssetsImagesFloor"
        src="./assets/images/floor.jpg"
      >

      <img
        id="AssetsImagesWall"
        src="./assets/images/wall.jpg"
      >

      <img
        id="AssetsImagesRoof"
        src="./assets/images/roof.jpg"
      >
    </a-assets>

    <a-light
      id="LightsAmbient"
      type="ambient"
      intensity="5"
    />

    <a-plane
      id="WallsFloor"
      src="#AssetsImagesFloor"
      rotation="-90 0 0"
      height="80"
      width="80"
      repeat="20 30"
      material="color: #333"
      static-body
    />

    <a-box
      v-for="({ name, position, rotation }, index) in fence"
      :id="`Fence_${name}_${index}`"
      :key="`Fence_${name}_${index}`"
      :position="position"
      :rotation="rotation"
      src="#AssetsImagesWall"
      height="2"
      width="30"
      repeat="5 1"
      material="color: #444"
      static-body
    />

    <a-box
      v-for="({ name, position, rotation }, index) in walls"
      :id="`Walls_${name}_${index}`"
      :key="`Walls_${name}_${index}`"
      :position="position"
      :rotation="rotation"
      src="#AssetsImagesWall"
      height="2"
      width="5"
      material="color: #444"
      static-body
    />

    <a-box
      id="Actor"
      ref="Actor"
      src="#AssetsImagesRoof"
      position="-12.5 1.1 -13"
      height="1.5"
      width="1.5"
      depth="1.5"
      material="color: #257"
      @collide="collided"
    />

    <a-entity
      id="Spectator"
      position="0 20 0"
      rotation="-90 0 0"
      movement-controls="speed: 1"
    >
      <a-entity
        id="SpectatorCamera"
        camera
        look-controls
      />
    </a-entity>
  </a-scene>
</template>

<script>
// import * as tf from "@tensorflow/tfjs";

export default {
  name: 'Maze',

  data() {
    return {
      fence: [
        {
          name: 'Front',
          position: '0 1 -15',
          rotation: '0 0 0',
        },
        {
          name: 'Left',
          position: '0 1 15',
          rotation: '0 180 0',
        },
        {
          name: 'Right',
          position: '-15 1 0',
          rotation: '0 90 0',
        },
        {
          name: 'Back',
          position: '15 1 0',
          rotation: '0 -90 0',
        },
      ],
      walls: [
        {
          name: '1',
          position: '-10 1 -12',
          rotation: '0 -90 0',
        },
        {
          name: '2',
          position: '-10 1 -7',
          rotation: '0 -90 0',
        },
        {
          name: '3',
          position: '-10 1 -2',
          rotation: '0 -90 0',
        },
        {
          name: '4',
          position: '-10 1 3',
          rotation: '0 -90 0',
        },
        {
          name: '5',
          position: '-10 1 8',
          rotation: '0 -90 0',
        },
      ],
      isFirstCollided: true,
    };
  },

  mounted() {
    console.log('Actor', this.$refs.Actor);
  },

  methods: {
    collided(e) {
      // Первое столкновение происходит при размещении объекта на поле.
      if (!this.isFirstCollided) {
        console.log('collided', e);
      }

      this.isFirstCollided = false;
    },
  },
};
</script>
