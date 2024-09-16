/*
 * Copyright 1996-2023 Cyberbotics Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdio.h>
#include <stdlib.h>
#include <webots/distance_sensor.h>
#include <webots/led.h>
#include <webots/motor.h>
#include <webots/robot.h>
#include <webots/emitter.h>
#include <time.h>

#define TIME_STEP 64
#define RANGE (127 / 2)


int main(int argc, char *argv[]) {
  /* define variables */

  WbDeviceTag emitter;

  /* initialize Webots */
  wb_robot_init();

  /* get and enable devices */
/*
  init_devices();

  /* get a handler to the motors and set target position to infinity (speed control). */
  emitter = wb_robot_get_device("Emitter");
  
  double message;
  struct timespec ts;

  while(wb_robot_step(TIME_STEP) != -1){
    clock_gettime(CLOCK_REALTIME, &ts);
    message = ts.tv_sec + ts.tv_nsec / 1e9;
    wb_emitter_send(emitter, &message, sizeof(message));
  }

  return 0;
}
