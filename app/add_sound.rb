# Adds App/silence.wav to the app target's bundle resources (run in CI after ios_patch.py).
require 'xcodeproj'
project = Xcodeproj::Project.open('ios/App/App.xcodeproj')
target = project.targets.find { |t| t.name == 'App' }
group = project.main_group['App']
ref = group.files.find { |f| f.path == 'silence.wav' } || group.new_file('silence.wav')
target.add_resources([ref]) unless target.resources_build_phase.files_references.include?(ref)
project.save
puts 'added silence.wav'
