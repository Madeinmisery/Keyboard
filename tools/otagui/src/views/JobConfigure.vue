<template>
  <!-- eslint-disable vue/no-v-model-argument -->
  <v-row>
    <v-col
      cols="12"
      md="6"
    >
      <OTAOptions
        v-model:isIncremental="isIncremental"
        :targetDetails="targetDetails"
        :incrementalSource="incrementalSource"
        :targetBuild="targetBuild"
      />
    </v-col>
    <v-divider vertical />
    <v-col
      cols="12"
      md="6"
      class="library"
    >
      <BuildLibrary
        v-model:incrementalSource="incrementalSource"
        v-model:targetBuild="targetBuild"
        v-model:targetDetails="targetDetails"
        :isIncremental="isIncremental"
      />
    </v-col>
  </v-row>
</template>

<script>
import OTAOptions from '@/components/OTAOptions.vue'
import BuildLibrary from '@/components/BuildLibrary.vue'

export default {
  components: {
    OTAOptions,
    BuildLibrary
  },
  data() {
    return {
      incrementalSource: '',
      targetBuild: '',
      targetDetails: [],
      isIncremental: false
    }
  },
}
</script>

<style scoped>
  .library {
    overflow: scroll;
    height:calc(100vh - 80px);
  }
</style>>