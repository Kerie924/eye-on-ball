const { withDangerousMod } = require('expo/config-plugins')

function withGradleWrapperTimeout(config) {
  return withDangerousMod(config, [
    'android',
    async (mod) => {
      const fs = require('fs')
      const path = require('path')
      const file = path.join(
        mod.modRequest.platformProjectRoot,
        'gradle/wrapper/gradle-wrapper.properties',
      )
      if (fs.existsSync(file)) {
        const next = fs
          .readFileSync(file, 'utf8')
          .replace(/networkTimeout=\d+/g, 'networkTimeout=120000')
        fs.writeFileSync(file, next)
      }
      return mod
    },
  ])
}

module.exports = withGradleWrapperTimeout
