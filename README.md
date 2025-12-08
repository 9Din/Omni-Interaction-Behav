

# Overview 

***Omni Interaction Behav***

> This script based on the Omniverse platform (door and lighting control extension) mainly revolves around the dynamic interaction of doors and lighting management in 3D scenes. Its functional features make it suitable for the following specific scenarios:

![showcase](readme_media/welcome.png)

1. Architectural visualization and interior design display
- In 3D models of architecture or interior design, the opening and closing effects of doors can be dynamically demonstrated through scripts (such as the sliding of single/double sliding doors, the rotation of swing doors), combined with the switching of lighting groups (such as adjusting the brightness and color temperature of different areas), to visually display spatial layout, traffic paths, and lighting effects to customers.
- For example, designers can select rooms through the UI, control door opening/closing animations, and switch lighting modes such as "day" and "night" to present real-time spatial atmospheres in different scenes.

2. Virtual simulation and interactive training
- In virtual simulation scenarios such as fire drills and building safety training, scripts can simulate the logic of door operations in real environments: students can interactively control the opening and closing of doors (such as opening and closing doors or pulling sliding doors in emergency situations), while lighting can be triggered in conjunction with the scene (such as emergency exit lights on), enhancing the immersion and realism of training.
- For example, in a fire drill, the emergency light is automatically triggered when the "safety exit" door is opened to help students familiarize themselves with the evacuation process.

3. Digital twins and intelligent space management
- In digital twin models of factories, shopping malls, and other places, scripts can simulate the automation control of doors (such as the "sliding on both sides" and "fixed on one side" modes of double sliding doors), and reflect space usage in conjunction with lighting group status (such as automatic dimming of lights when conference room doors are closed).
- For example, in the digital twin system of a shopping mall, the opening and closing states of different store doors are controlled through scripts, and the "open" (lit) and "closed" (unlit) states are distinguished by the color of the lights.

4. 3D Education and Teaching Demonstration
- In architecture and machinery, scripts can assist in explaining the structural types of doors (such as the mechanical principles of sliding doors and swing doors): displaying the motion trajectory of the door (translation/rotation) through animation, and focusing on the details of the door panel with lighting.
- For example, the building can switch door types through the UI, demonstrate the force balance when sliding on both sides of a double sliding door, and highlight the sliding track of the door panel with lights.

<br>


<br>

## Quick Start

**Target applications:** NVIDIA Omniverse App

**Supported OS:** Windows and Linux

**Changelog:** [CHANGELOG.md](exts/omni.LightingControl/docs/CHANGELOG.md)

**Table of Contents:**

- [User Guide](#guide)
  - [Preparation](#guide-Preparation)
- [Extension usage](#usage)
  - [Dependencies](#usage-Dependencies)
  - [Adding Extension](#usage-Adding)
- [Usage Tips](#tips)
  - [Lighting Management Process](#tips-Light)
  - [Door Usage Process](#tips-door)
  - [Troubleshooting](#tips-fault)
- [Video](#video)
- [Precautions](#precautions)


<br>

![showcase](exts/omni.InteractionBehav/data/preview.png)

<hr>

**Core Capabilities**
This script is an extension of USD scene interaction control based on the Omniverse platform, and its core capabilities can be summarized as follows:
1. Intelligent parsing of USD scene elements: By traversing the USD stage prim structure, automatically identifying scene elements containing specific keywords (such as "D_oor"), parsing the hierarchical structure, type attributes (single/double sliding doors, single/double swing doors), and spatial parameters (width, orientation axis) of doors, achieving structured extraction and classification of door components.
2. Door dynamic behavior control: Based on the analysis of door types and parameters, provide parameterized animation control capabilities - support sliding doors to move along the X/Z axis (including single leaf full width sliding, double leaf single-sided fixed/double-sided split sliding modes), swing doors to rotate around the Y axis (including angle and direction adjustment), achieve 60FPS smooth animation through asynchronous interpolation calculation, and maintain animation state locks to avoid concurrent conflicts.
3. Full lifecycle state management: Record the initial transformation state (translation, rotation attributes) and target state of the door body, support reversible execution of door opening/closing actions, provide animation interruption and forced reset mechanisms, ensure consistency and controllability of scene interaction.
4. Scene association and interaction integration: Through path search and room level association, realize the binding management of doors and spaces; Build a visual interactive interface by combining UI components (drop-down selection, operation buttons), supporting users to retrieve scene paths and trigger door control through room selection, forming a complete interactive loop of "recognition parsing control feedback".
5. Cross component collaboration capability: Reserved lighting control interface, supporting the association of lighting and door status through room paths, providing an extended foundation for the linkage between scene lighting and spatial interaction, and adapting to the complex scene control requirements of multi-element collaboration.

<br>
<hr>

<a name="guide"></a>
## 🎯 User Guide
<a name="guide-Preparation"></a>
### Preparation

**Light Control**

* organization structure: 
- Ensure that the lights in the scene are organized according to the following structure

```
        LightManager   
        # Directory Structure

        /World/
            ├── lights/                         # Root Path
                ├── LivingRoom/                 # Room (Secondary Catalog)
                │   ├── CeilingLights/          # Lighting Group (Level 3 Catalog)  
                │   │   │   ├── SpotLight1      # Specific Lighting
                │   │   │   └── SpotLight2
                │   └── AccentLights/
                │           └── CylinderLight
                └── Bedroom/
                    └── BedsideLights/
                            └── DiskLight
                
```

**Access Control**

- Ensure that the doors in the scene are organized according to the following structure
```


    /World/
        room/                            #① room name
        ├── {xx_Door}/                   #② door name
        │   ├── assembly/                #③ door frame and decoration on door frame
        │   │   ├── other geometry       #④ frame
        │   └── Panel_Dual_Sliding/      #⑤ door leaf assembly、door panel
        │   │   ├── panel_left/          #⑥ left door leaf
        │   │   │   └── other/           #⑦ decorative items on the door  
        │   │   ├── panel_right/         #⑧ right door leaf
        │   │   │   └──  other/          #⑨ decorative items on the door

    ② "_Door " keywords,To confirm if there are any doors in this room that need to be opened.
    ⑤ "Panel_Dual_Sliding" keywords,Determine the type of door that needs to be opened.
              
            4 types:
            Panel_Single_Sliding
            Panel_Single_Pivot
            Panel_Dual_Sliding
            Panel_Dual_Pivot


    example:

    /World
        Bedroom
        ├── Bedroom_Door       
        │   ├── assembly                     
        │   │   ├── other                         
        │   └── Panel_Dual_Pivot                    
        │   │   ├── Panel_Left
        │   │   │   └── handle                  
        │   │   ├── Panel_Right
        │   │   │   └── handle     


    /World/
      LivingRoom/
        ├── MainEntrance_Door/                  
        │   ├── Panel_Single_Sliding/           
        │   │   └── Panel/                     
        │   └── DoorFrame/                      
        └── Patio_Door/
            ├── Panel_Dual_Sliding/
            │   ├── Panel_Left/
            │   └── Panel_Right/
            └── SlidingTrack/  
    
```



<br>
<hr>

<a name="usage"></a>
### Extension usage

<a name="usage-Dependencies"></a>
#### Dependencies
- Requires Omniverse Kit >= 108

<a name="usage-Adding"></a>
### Adding This Extension
To add this extension to your Omniverse app:

1. `Developer` > `Extensions` or `Window` > `Extensions`
2. ☰ > Settings
3. ✚ Add `git:https://github.com/9Din/omni_Lighting_Control/tree/main/exts` folder to the Extension Search Paths
4. The user extension should appear on the left
5. `Autoload` needs to be checked for the FileFormat plugin to be correctly loaded at USD Runtime.
        
Manual installation:

1. Download Zip  ` git clone https://github.com/9Din/omni_Lighting_Control.git `
2. Extract and place into a directory of your choice
3. `Developer` > `Extensions` or `Window` > `Extensions`
4. ☰ > Settings
5. ✚ Add `\omni_Lighting_Control\exts` folder to the Extension Search Paths
6. The user extension should appear on the left
7. `Autoload` needs to be checked for the FileFormat plugin to be correctly loaded at USD Runtime.
<br>
<hr>

<a name="tips"></a>
## 🗒️ Usage Tips

<a name="tips-Light"></a>
### 💡 Lighting Management Process 

1. Search for lighting structure
- Enter the root path of the light in the path box
- click Search button
- The system automatically recognizes rooms and lighting groups
2. Select the lights to be controlled
- Select a room from the "Select Room" dropdown menu
- Select a lighting group from the "Select Lighting" dropdown menu
- All lights in this group will be automatically selected
3. Adjust lighting properties
- Use sliders or directly input numerical values to adjust parameters
- The modification takes effect immediately and can be viewed in real-time in the viewport
4. Save personal presets
- After adjusting to the desired effect, click on "Record Defaults"
- Afterwards, it can be restored at any time through 'Reset to Defaults'
<br>
*Color control (disabled)

<a name="tips-door"></a>
### 🚪 Tips for using door control system
#### Preparation of scene structure

1. The door control system relies on naming conventions, please ensure that the doors in the scene comply with the following naming rules:

- The name of the door group must contain the keyword 'D_Door', for example: Entrance_Soor.
- The door group should be located under the room (Xform), and the room should be located under/World/.
- Click the "Search Doors" button, and the system will automatically search for all door groups containing the keyword "_Soor" in the/World/path, and list the rooms.

2. The system supports four types of doors:

- Panel_Single_Sliding: Single Sliding Door
- Panel_Single_Pivot: Single Pivot Door
- Panel_Dual_Sliding: Dual Sliding Door
- Panel_Dual_Pivot: Dual Pivot Door

3. Parameter Introduction：

- Slide Distance: Sliding distance (in centimeters). The default sliding distance for a single sliding door is the width of the door, while for a double sliding door, the default sliding distance is half the width of the door (both sides mode).
- Door Orientation: The direction of the door. Choose whether the door slides along the X-axis or Z-axis. The system will automatically detect it, but it can also be manually overwritten.
- Direction: Push or Pull. Determine the direction of the door's movement.
- Dual Sliding Mode: The opening mode of a double sliding door. There are three modes:
  > Left Fixed: Left fan fixed, right fan sliding
  Right Fixed: Right fan fixed, left fan sliding
  Both Sides: Slide both sides simultaneously (default)
- Pivot Angle: Rotation angle (unit: degrees). Default 90 degrees.
- Direction: Push or Pull. Determine the direction of rotation of the door.
- Speed Regulation: animation speed multiplier. 1.0 is the normal speed, slower if it is less than 1.0, and faster if it is greater than 1.0.

4. Operating door

- Open Door: Click the "Open Door" button to open the door in an animated format. During the door opening process, you can click the "Pause" button to pause the animation.
- Closing the door: Click the "Close Door" button to close the door in an animated form.
- Pause: Click the "Pause" button to stop the animation of the current door.

<br>
**Precautions**

- The door control system relies on the initial state record of the door. If the door in the scene is already open, it is recommended to manually close it first to ensure that the system correctly records the initial state.
- If the structure of the door does not meet the standards, the system may not be able to correctly identify the door panel. Please ensure that the naming of the panel includes keywords such as' left ',' right ', or' single '.

<a name="tips-fault"></a>
### ⚠️ Troubleshooting

1. The light cannot be found
- Confirm if the path is correct and if there are Xform type rooms along the path.
- Check if the light types are supported (SphereLight, RectLight, DiskLight, CylinderLight, DomeLight, DistantLight).
2. The door cannot be recognized
- Confirm if the door group name contains' _Soor '.
- Check if the door group is located in the room under/World/.

<br>
<a name="video"></a> 

![Sample Video](readme_media/record_1.mp4)

<!--
<hr>

<a name="tips-core"></a>

## Core computing logic

**1. Lighting control part**
<!--
> Color and intensity control
The color of the light is controlled by the three components of RGB, with each component within the range of [0,1]. Intensity and exposure are multiplicative factors, and the final illumination output can be expressed as:

\begin{array}{l}
\text { basecolor } C_{0}=\left(R_{0}, G_{0}, B_{0}\right) \text { ，intensity } I_{0} \text { ，exposure } E_{0} \text { ， adjusted color is：}\\
C_{\text {adjusted }}=\left(R_{0} \times I \times 10^{E}, G_{0} \times I \times 10^{E}, B_{0} \times I \times 10^{E}\right)
\end{array}

Among them, I and E are the adjusted intensity and exposure values. Note: In actual rendering, exposure usually affects brightness exponentially
-->
<hr>

<a name="precautions"></a>

### ⚠️ Precautions

1. Permission requirement: Some operations require write permission for the scene
2. Revocation restriction: Revocation of material deletion can only be effective in the current session
3. Performance considerations: In large scenes, material scanning may take a long time
4. Backup suggestion: It is recommended to backup important scenarios before batch deletion operations



