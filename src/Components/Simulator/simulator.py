import simulator_init
import os
import unittest
from clock import Clock

from factories.animal_factory import AnimalFactory
from factories.sensor_factory import SensorFactory
from render_manager import RenderedState

class TestConfig(simulator_init.TestConfig):
    def __init__(self, *args, config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

class Simulator():
    def __init__(self) -> None:
        self.config = simulator_init.Config()
        self.clock  = Clock(step_interval=float(os.environ['STEP_INTERVAL'])) # 200 step interval 200 milliseconds

    # run the live simulators
    def execute(self):
        
        # initialse the simulator configuration
        animals = self.config.initialise()

        # render state
        if bool(os.environ['SIMULATOR_LOOPS']):
            self.render_state = RenderedState()
            self.render_state.render_initial_sensor_state(self.config, animals)
    
        # start the simulator loop
        self.main_loop(animals, loops=int(os.environ['SIMULATOR_LOOPS']))
        
    def main_loop(self, animals, loops=10):
        while self.config.system_manager.state:
            for _ in range(loops):
                if bool(os.environ['SYSTEM_PAUSE']): self.config.system_manager.pause()
                # update the simulated time (advance the clock)
                self.clock.update()
                
                for animal in animals:
                    
                    # update the animal lla
                    animal.update_lla()
                    
                    # generate random animal vocalisation
                    if animal.random_vocalisation():
                        self.render_state.render_animal_vocalisation(animal)
                        predicted_lla = self.config.SENSOR_MANAGER.vocalisation(animal)
                        
                        self.config.comms_manager.mqtt_send_random_audio_msg(animal, predicted_lla)

                    animal.describe()
                
                # render state to map
                self.render_state.render(animals)
                
                # process API commands
                self.process_api_commands()
                
                # wait for wall clock to elapse to sync with real time
                self.wait_real_time_sync()

                if bool(os.environ['SYSTEM_STOP']):
                    break

        
    def process_api_commands(self):
        # TODO
        pass
    
    def wait_real_time_sync(self):
        self.clock.wait_real_time_sync()
      
    # run some simulator test cases
    def test(self):
        suite = unittest.TestSuite()
        for test_name in unittest.defaultTestLoader.getTestCaseNames(TestConfig):
            suite.addTest(TestConfig(test_name, config=self.config))

        unittest_runner = unittest.TextTestRunner()
        unittest_runner.run(suite)

        self.SystemClock = Clock()
        self.AnimalFactory = AnimalFactory()
        self.SensorFactory = SensorFactory()
        print(f'Random animal create(): {self.AnimalFactory.create().species}')
        print(f'Random animal create_random_animal(): {self.AnimalFactory.create_random_animal().species}')

if __name__ == "__main__":
    
    #clock = Clock()
    #clock.test()
    
    #mm = CommsManager()
    #mm.initialise_communications()
    #mm.test()
    
    sim = Simulator()
    #sim.test()
    sim.execute()
    
    