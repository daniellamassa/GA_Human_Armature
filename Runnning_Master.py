import random
import pickle
import time
import subprocess
import os

generations = []
best_fitness = []


class ArmatureAnimation:
    """
    Animation class encoding the primary bones in a rigged model in blender.
    """
    def __init__(self, length):
        self.fitness = 0
        self.rules = []
        self.WalkCycle = []
        self.length = length
        self.seed = {"Lower Arm.R": [0, 0, 0],
                     "Upper Arm.R": [-.411, .085, .049],
                     "Lower Arm.L": [0, 0, 0],
                     "Upper Arm.L": [-.411, -.085, -.049],
                     "Lower Leg.R": [0, 0, 0],
                     "Upper Leg.R": [0, 0, 0],
                     "Lower Leg.L": [0, 0, 0],
                     "Upper Leg.L": [0, 0, 0],
                     "Torso": [0, 0, 0],
                     "Chest": [0, 0, 0]}

    def make_rand_rule(self):
        """
        Creates a new random rule for each bone in the armature. These rules
        encode by how much joints move between keyframes.
        """
        bone_names = ["Lower Arm.R", "Upper Arm.R", "Lower Arm.L", "Upper Arm.L", "Lower Leg.R", "Upper Leg.R",
                      "Lower Leg.L",
                      "Upper Leg.L", "Torso", "Chest"]
        new_rule = {}
        for bone in bone_names:
            x_rule = ((random.random() - 0.5) / 3)
            y_rule = ((random.random() - 0.5) / 3)
            z_rule = ((random.random() - 0.5) / 3)
            new_position = [x_rule, y_rule, z_rule]
            new_rule[bone] = new_position
        self.rules.append(new_rule)

    def create_rand_rules(self):
        """
        Creates a full set of rules for the walk cycle.
        """
        self.rules = []
        for count in range(0, self.length):
            self.make_rand_rule()

    def make_anim_cycle(self):
        '''
        Applies each rule in the rule set procedurally to generate the Walk Cycle
        '''
        poseOne = self.seed
        self.WalkCycle = [poseOne] #First pose is always seed
        for rule in self.rules:
            next_pose = self.apply_rules(self.rules[-1], rule)
            self.WalkCycle.append(next_pose)

    def evaluate_fitness(self):
        """
        Arbirary fitness function awarding points for sorted x,y,z bone data.
        Used to test the GA outside of Blender.
        """
        self.fitness = 0
        for pose in self.WalkCycle:
            for key in pose.keys():
                copy = pose[key].copy()
                copy.sort()
                if (pose[key] == copy):
                    self.fitness += 1

    def apply_rules(self, prev_pose, rule):
        '''
        Takes a previous pose and a rule, and sums the values at for each x, y, and z value,
        generating the next pose in .
        '''
        new_pos = {}
        for key in prev_pose.keys():
            one_bone_values = []
            for count in range(0, 3):
                next_value = prev_pose[key][count] + rule[key][count]
                if next_value > 1:
                    next_value = 1
                if next_value < -1:
                    next_value = -1
                one_bone_values.append(next_value)
            new_pos[key] = one_bone_values
        return new_pos

    def crossover(self, other):
        """
        Takes a second individual as a parameter and crosses over thier rule sets, returning the
        two crossed over Armature Animations. 
        """
        # assert len(self.rules)== len(other.rules)
        # assert len(self.rules) != 0
        new_rule_one = []
        new_rule_two = []

        pivot = random.randint(0, self.length)
        for count in range(0, self.length):
            if count > pivot:
                new_rule_one.append(self.rules[count])
                new_rule_two.append(other.rules[count])
            else:
                new_rule_one.append(other.rules[count])
                new_rule_two.append(self.rules[count])

        c1 = ArmatureAnimation(self.length)
        c2 = ArmatureAnimation(self.length)

        c1.take_rules(new_rule_one)
        c1.make_anim_cycle()
        c1.evaluate_fitness()

        c2.take_rules(new_rule_two)
        c2.make_anim_cycle()
        c2.evaluate_fitness()
        assert (len(c1.rules) == 30)
        assert (len(c2.rules) == 30)
        return c1, c2

    def copy_self(self):
        """
        Returns a copy of the Armature Animation
        """
        copy = ArmatureAnimation(self.length)
        copy.take_rules(self.rules)
        copy.evaluate_fitness()
        return copy

    def mutate(self, mut_prob):
        """
        Mutates the current indidual with a mut_prob passed in as a paremeter.
        """
        new_rules = []
        if random.random() < mut_prob:
            for rule in self.rules:
                a_new_rule = {}
                for key in rule.keys():
                    new_bone_pose = []
                    for idx in range(0, 3):
                        a_quaternary = rule[key][idx] + random.random() / 2 - .25
                        if a_quaternary > 1:
                            a_quaternary = 1
                        if a_quaternary < -1:
                            a_quaternary = -1
                        new_bone_pose.append(a_quaternary)
                    a_new_rule[key] = new_bone_pose
                new_rules.append(a_new_rule)
            self.rules = new_rules
            self.make_anim_cycle()
            self.evaluate_fitness()
            #print(len(self.rules))
        assert len(self.rules) == 30

    def take_rules(self, rules):
        """
        Takes an already generated rule set and sets it as the ArmatureAnimations rules. 
        """
        self.rules = rules


class Population:
    """
    Population Class encoding methods for a genetic algorith on a population of Armature Animations. 
    """
    def __init__(self, pop_size, max_gens, num_elites, xOver_prob, mut_prob):
        self.size = pop_size
        self.max_gens = max_gens
        self.num_elites = num_elites
        self.xOver_prob = xOver_prob
        self.mut_prob = mut_prob

        self.pop = []
        self.fits = []
        self.best_fit = 0
        self.weights = []

    def run_ga(self):
        """
        Runs the genetic algorith with the paremetes passed into the population at creation
        """
        gens = 1
        #Creates the initial first generation population
        for index in range(0, self.size):
            random_cycle = ArmatureAnimation(30)
            random_cycle.create_rand_rules()
            random_cycle.make_anim_cycle()
            self.pop.append(random_cycle)

        #for member in self.pop:
            #print(len(member.rules))

        while (gens < self.max_gens):
            print("Popsize is:", len(self.pop))
            next_pop = []
            #### Use pickling and blender to generate members fitness

            for idx in range (self.num_elites,self.size):
                self.pop[idx].fitness = 0
                

            pfile_population = open('pickled_population.txt', 'wb') ### Empties location for pickled population
            pfile_population.truncate(0)
            pickle.dump(self.pop, pfile_population)
            pfile_population.close()

            file_indicator = open('indicator.txt', 'wb')
            file_indicator.truncate(0)
            file_indicator.close()

            ######Call blender_helper
            os.system("sudo Blender --background /Users/jamesbrouder/Desktop/483_Final_Project/Helper_Executable.blend --python Users/jamesbrouder/Desktop/483_Final_Project/Blender_Helper.py")
            subprocess.run(["sudo","/Applications/Blender/blenderplayer.app", "--background", "/Users/jamesbrouder/Desktop/483_Final_Project/Helper_Executable.blend", "--python", "/Users/jamesbrouder/Desktop/483_Final_Project/Blender_Helper.py"])
            gen_done = False ####Waits for status change from blender script
            while not gen_done:
                file_indicator = open('indicator.txt', 'rb')
                lines = file_indicator.readlines()
                print("Fitness Calculations Incomplete")
                if len(lines)!=0:
                    gen_done = True
                    print("Blender Calculation Complete")
                file_indicator.close()
                time.sleep(2)

            ####
            pfile_population = open('pickled_population.txt', 'rb')
            Population = pickle.load(pfile_population)
            pfile_population.close()


            self.pop = Population
            #print("Popsize is:", len(self.pop))

            #print(len(self.pop))
            #for member in self.pop:
                #print(len(member.rules))
                
            self.sort_and_structure_pop()

            for idx in range(0, self.num_elites):
                next_pop.append(self.pop[idx])
                #print(self.pop[idx].fitness)
        
            #print(len(next_pop))

            while (len(next_pop) < self.size):
                p1 = self.weighted_select()
                p1.fitness = 0
                p1.mutate(self.mut_prob)

                p2 = self.weighted_select()
                p2.fitness = 0
                p2.mutate(self.mut_prob)

                if random.random() < self.xOver_prob:
                    c1, c2 = p1.crossover(p2)
                else:
                    c1 = p1.copy_self()
                    c2 = p2.copy_self()

                c1.make_anim_cycle()
                next_pop.append(c1)

                if (len(self.pop) < self.size):
                    c2.make_anim_cycle()
                    next_pop.append(c2)

            self.pop = next_pop
            #for member in self.pop:
                #print(type(member))
            self.sort_and_structure_pop()
            # for indivdual in self.pop:
            # print(len(indivdual.rules))
            # print(self.fits)

            
            print("____________________")
            print("Generation Complete:", gens)
            print("Best Fitness:", self.best_fit)
            average = 0
            count = 0
            
            for member in self.pop:
                average+= member.fitness
                #print(member.fitness)
                count += 1
                
            print("Average Fitness:", average/count)
            generations.append(gens)
            best_fitness.append(self.best_fit)
            # print(generations)
            # print(best_fitness)
            gens += 1

        return


    def sort_and_structure_pop(self):
        self.pop = sorted(self.pop, key=lambda g: g.fitness, reverse=True)

        self.fits = []
        for member in self.pop:
            fitness = member.fitness
            if fitness > self.best_fit:
                self.best_fit = fitness
            self.fits.append(member.fitness)

        self.weights = []
        for member in self.pop:
            self.weights.append(member.fitness / self.best_fit)
        self.best_fit = self.fits[0]
        return

    def weighted_select(self):

        weighted_member = random.choices(self.pop, weights=self.weights, k=1)[0]

        return weighted_member.copy_self()

    def test_weighted_select(self):
        for index in range(0, self.size):
            random_cycle = ArmatureAnimation(30)
            random_cycle.create_rand_rules()
            random_cycle.make_anim_cycle()
            random_cycle.evaluate_fitness()
            self.pop.append(random_cycle)
        self.sort_and_structure_pop()
        
        print("Average is", sum(self.fits) / len(self.fits))

        for count in range(0, 50):
            p1 = self.weighted_select()
            p2 = self.weighted_select()
            print("Member, selected from wheel, has fitness of:", p1.fitness)
            print("Member, selected from wheel, has fitness of:", p2.fitness)
            c1, c2 = p1.crossover(p2)
            print("Member, selected via crossover, has fitness of:", c1.fitness)
            print("Member, selected via crossover, has fitness of:", c2.fitness)


Population = Population(20, 100, 4, 1, 1)
# Population.TestWeightedSelect()
print("Now running GA")
Population.run_ga()
# print(population.fits)
