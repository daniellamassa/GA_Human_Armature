import bpy
import random
import pickle

def select_object(name):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.window.scene.objects:
        if (obj.name == name):
            bpy.context.view_layer.objects.active = obj
            return
    print("No such object")
    return

class ArmatureAnimation:
  """
  Animation class encoding the primary bones in a rigged model in blender.
  """
  def __init__(self, length):
    self.fitness = 0
    self.rules = []
    self.WalkCycle = []
    self.length = length
    self.seed = {"Lower Arm.R": [0,0,0],
         "Upper Arm.R": [-.411, .085, .049],
         "Lower Arm.L": [0,0,0],
         "Upper Arm.L": [-.411, -.085, -.049],
         "Lower Leg.R": [0,0,0],
         "Upper Leg.R": [0,0,0],
         "Lower Leg.L": [0,0,0],
         "Upper Leg.L": [0,0,0],
         "Torso": [0,0,0],
         "Chest": [0,0,0]}

  def make_rand_rule(self):
      """
      Creates a new random rule for each bone in the armature. These rules
      encode by how much joints move between keyframes.
      """
      bone_names = ["Lower Arm.R", "Upper Arm.R", "Lower Arm.L", "Upper Arm.L", "Lower Leg.R", "Upper Leg.R", "Lower Leg.L",
      "Upper Leg.L",  "Torso", "Chest"]
      new_rule = {}
      for bone in bone_names:
          x_rule = ((random.random()-0.5))
          y_rule = ((random.random()-0.5))
          z_rule = ((random.random()-0.5))
          new_position = [x_rule, y_rule, z_rule]
          new_rule[bone] = new_position
      self.rules.append(new_rule)

  def create_rand_rules(self):
    """
    Creates a full set of rules for the walk cycle.
    """
    for count in range (0, self.length):
      self.make_rand_rule()

  def make_anim_cycle(self):
    '''
    Applies each rule in the rule set procedurally to generate the Walk Cycle
    '''
        
    poseOne = self.seed
    self.WalkCycle = []
    self.WalkCycle.append(poseOne)
    for rule in self.rules:
      next_pose = self.apply_rules(self.rules[-1], rule)
      self.WalkCycle.append(next_pose)
      #print("Walk cycle lenght of", len(self.WalkCycle))

  def apply_rules(self, prev_pose, rule):
    '''
    Takes a previous pose and a rule, and sums the values at for each x, y, and z value,
    generating the next pose in.
    '''
    new_pos = {}
    for key in prev_pose.keys():
      one_bone_values = []
      for count in range(0,3):
        next_value = prev_pose[key][count] + rule[key][count]
        if next_value > 1:
          next_value = 1
        if next_value < -1:
          next_value = -1
        one_bone_values.append(next_value)
      new_pos[key] = one_bone_values
    return new_pos
    
  def apply_pose_as_shapekey(self, a_pose):
      """Applies a given pose as a shape key, a purely mesh based animation type"""
      select_object("Armature")
      bpy.ops.object.posemode_toggle()
      for bone in a_pose.keys():
        angles = a_pose[bone]
        bpy.context.object.pose.bones[bone].rotation_quaternion[1] = angles[0]
        bpy.context.object.pose.bones[bone].rotation_quaternion[2] = angles[1]
        bpy.context.object.pose.bones[bone].rotation_quaternion[3] = angles[2]
        
      select_object("Body")
      bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier="Armature")
      
  def apply_shapekey_animation(self):
      """
      Sets keyframes correctly interpolating between previously generated
      all shape keys stored in bpy.data.shape_keys().
      """
      pose_list = []
      for key_name in bpy.data.shape_keys["Key"].key_blocks.keys():
          pose_list.append(key_name)
      
      time = 0
      
      for interval in range(1, len(pose_list)-1):
          #print("The pose is:", pose_list[interval])
          bpy.context.scene.frame_current = time
          
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval+1]].value = 0
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval+1]].keyframe_insert("value", frame=time)
          
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval]].value = 1
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval]].keyframe_insert("value", frame=time)
          
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval-1]].value = 0
          bpy.data.shape_keys["Key"].key_blocks[pose_list[interval-1]].keyframe_insert("value", frame=time)
          
          time += 8
          

#Loads in the Population.pop list from the master script

pfile_population = open('/Users/jamesbrouder/Desktop/483_Final_Project/pickled_population.txt', 'rb')
Population = pickle.load(pfile_population)
pfile_population.close()

return_population = []

print("BREAKING")
print("Population Length is ", len(Population))
for ACycle in Population:
    print(ACycle.fitness)
    #For each member of the population, execute the following blender steps to evaluate fitness.
    if ACycle.fitness != 0:
        return_population.append(ACycle)
        print("do I take them all")
    else:
        print("THE length is ", len(ACycle.rules))
        print(len(ACycle.rules)> 30)
        ACycle.make_anim_cycle()

        select_object("Body")
        bpy.ops.object.shape_key_remove(all=True)
        bpy.ops.object.posemode_toggle()

        for a_pose in ACycle.WalkCycle:
          ACycle.apply_pose_as_shapekey(a_pose)
        ACycle.apply_shapekey_animation()

        #Clears data from Armature so it can be used for the next individual.
        select_object("Armature")
        bpy.ops.object.posemode_toggle()
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()

        select_object("Body")

        #Contextualizes data so that F-curve information can be parsed.
        context = bpy.context
        scene = context.scene
        object = context.object
        frame = scene.frame_start

        #Iterates through f-curves, stores animation data, applying each frame without playing
        # the animation in real time.
        while frame <= scene.frame_end:
            scene.frame_set(frame)
            for fcurve in object.data.shape_keys.animation_data.drivers.values():
                object.data.shape_keys.keyframe_insert(fcurve.data_path)
            frame = frame + 1

        #Selects the Plane.001 obj used to track armature motion.
        select_object("Plane.001")
        obj = bpy.context.active_object
        coords = [(obj.matrix_world @ v.co) for v in obj.data.vertices]
        print("The coords are:", coords[0][0])

        ACycle.fitness = coords[0][0]#Sets the fitness as the x value after the animation is complete.
        return_population.append(ACycle)

        #Resets all shape key data so it does not interfere with the basis frame when keys are removed. 
        for key_name in bpy.data.shape_keys["Key"].key_blocks.keys():
            bpy.data.shape_keys["Key"].key_blocks[key_name].value = 0

        

print(len(return_population))
pfile_population = open('/Users/jamesbrouder/Desktop/483_Final_Project/pickled_population.txt', 'wb')
pfile_population.truncate(0) ### Empties location for pickled population
pickle.dump(return_population, pfile_population)
pfile_population.close()

file_indicator = open('/Users/jamesbrouder/Desktop/483_Final_Project/indicator.txt', 'w')
file_indicator.write("Generation Complete, returning to master")
print("Generation Complete, returning to master")
file_indicator.close()
