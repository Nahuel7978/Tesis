
class StreamInterceptor:
    """Intercepta stdout para capturar las métricas de SB3"""
    
    def __init__(self, original_stream, metrics_capture):
        self.__original_stream = original_stream
        self.__metrics_capture = metrics_capture
        
    def write(self, text):
        # Escribir a la consola original
        self.__original_stream.write(text)
        self.__original_stream.flush()
        
        # Procesar líneas para capturar métricas
        for line in text.splitlines():
            if line.strip():
                self.__metrics_capture.process_output_line(line)
        
        return len(text)
    
    def flush(self):
        self.__original_stream.flush()
    
    def __getattr__(self, name):
        return getattr(self.__original_stream, name)