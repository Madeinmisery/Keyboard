<template>
  <form @submit.prevent="sendForm">
    <FileSelect
      v-if="input.isIncremental"
      v-model="incrementalSource"
      label="Select the source file"
      :options="targetDetails"
    />
    <FileSelect
      v-model="targetBuild"
      label="Select a target file"
      :options="targetDetails"
    />
    <OTAOptions
      :targetDetails="targetDetails"
      :targetBuilds="[targetBuild]"
      @update:input="input=$event"
    />
    <v-divider class="my-5" />
    <v-btn
      block
      type="submit"
    >
      Submit
    </v-btn>
  </form>
</template>

<script>
import OTAOptions from '@/components/OTAOptions.vue'
import FileSelect from '@/components/FileSelect.vue'
import { OTAConfiguration } from '@/services/JobSubmission.js'

export default {
  components: {
    OTAOptions,
    FileSelect,
  },
  props: {
    targetDetails: {
      type: Array,
      default: () => [],
    }
  },
  data() {
    return {
      incrementalSource: '',
      targetBuild: '',
      input: new OTAConfiguration(),
    }
  },
  computed: {
    checkIncremental() {
      return this.input.isIncremental
    },
  },
  watch: {
    checkIncremental: {
      handler: function () {
        this.$emit('update:isIncremental', this.checkIncremental)
      },
    },
  },
  created() {
    this.$emit('update:isIncremental', this.checkIncremental)
    this.$emit('update:Handler', this.setIncrementalSource, this.setTargetBuild)
  },
  methods: {
    /**
     * Send the configuration to the backend.
     */
    async sendForm() {
      try {
        let response_message = await this.input.sendForm(
          this.targetBuild, this.incrementalSource)
        alert(response_message)
        this.input.reset()
      } catch (err) {
        alert(
          'Job cannot be started properly for the following reasons: ' + err
        )
      }
    },
    setIncrementalSource (build) {
      this.incrementalSource = build
    },
    setTargetBuild (build) {
      this.targetBuild = build
    }
  },
}
</script>