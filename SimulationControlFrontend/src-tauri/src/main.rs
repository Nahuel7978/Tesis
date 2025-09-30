// src-tauri/src/main.rs

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    Manager, // Necesario para obtener la ventana ('get_window')
    Size,
    LogicalSize,
    PhysicalSize, // (Opcional) si prefieres trabajar con píxeles físicos
};

fn main() {
    tauri::Builder::default()
        // 🚀 La función .setup() es donde se ejecuta el código después de que la app se inicializa.
        .setup(|app| {
            // 1. Obtenemos la ventana principal. Asumimos que su etiqueta es 'main'.
            //    Si usaste un 'label' diferente en tauri.config.json, cámbialo aquí.
            let main_window = app.get_webview_window("main").expect("No se encontró la ventana principal");

            // 2. Intentamos obtener la información del monitor principal.
            if let Some(monitor) = main_window.primary_monitor().unwrap() {
                // Obtenemos el tamaño del área de trabajo (excluye barra de tareas, etc.)
                let size = monitor.size(); 
                let scale_factor = monitor.scale_factor(); // Factor de escala (ej: 1.5, 2.0)

                // 3. Calculamos las nuevas dimensiones.
                //    Ejemplo: Usaremos el 85% del área de trabajo disponible.
                let target_percentage: f64 = 0.85; 

                // Convertimos el tamaño físico a lógico (DIPs) para un redimensionamiento correcto.
                // y aplicamos el porcentaje.
                let physical_size = PhysicalSize::new(size.width, size.height);
                let logical_size: LogicalSize<f64> = physical_size.to_logical(scale_factor);

                let new_width = logical_size.width * target_percentage;
                let new_height = logical_size.height * target_percentage;

                // 4. Establecemos el nuevo tamaño de la ventana.
                main_window.set_size(Size::Logical(LogicalSize {
                    width: new_width,
                    height: new_height,
                }))
                .expect("Error al establecer el tamaño de la ventana");

                // 5. Opcional: Centrar la ventana después de redimensionar.
                main_window.center()
                    .expect("Error al centrar la ventana");
            } else {
                // Manejo de error si no se encuentra el monitor, 
                // la ventana se quedará con el tamaño predeterminado de tauri.config.json.
                eprintln!("No se pudo obtener el monitor primario, usando dimensiones por defecto.");
            }

            // El setup debe retornar un Result.
            Ok(()) 
        })
        .run(tauri::generate_context!())
        .expect("Error al ejecutar la aplicación Tauri");
}
