<template>
  <form @submit.prevent="sendForm">
    <FileList
      v-model="incrementalSources"
      :disabled="!input.isIncremental"
      label="Source files"
    />
    <v-divider />
    <FileList
      v-model="targetBuilds"
      label="Target files"
    />
    <v-divider />
    <OTAOptions
      :targetDetails="targetDetails"
      :targetBuilds="targetBuilds"
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
import FileList from '@/components/FileList.vue'
import { OTAConfiguration } from '@/services/JobSubmission.js'

export default {
  components: {
    OTAOptions,
    FileList,
  },
  props: {
    targetDetails: {
      type: Array,
      default: () => [],
    }
  },
  data() {
    return {
      incrementalSources: [],
      targetBuilds: [],
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
    this.$emit('update:Handler', this.addIncrementalSources, this.addTargetBuilds)
  },
  methods: {
    /**
     * Send the configuration to the backend.
     */
    async sendForm() {
      try {
        let response_message = await this.input.sendForms(
          this.targetBuilds, this.incrementalSources)
        alert(response_message)
        this.input.reset()
      } catch (err) {
        alert(
          'Job cannot be started properly for the following reasons: ' + err
        )
      }
    },
    addIncrementalSources (build) {
      if (!this.incrementalSources.includes(build)) {
        this.incrementalSources.push(build)
      }
    },
    addTargetBuilds (build) {
      if (!this.targetBuilds.includes(build)) {
        this.targetBuilds.push(build)
      }
    }
  },
}
</script>