
"""Registro de costos estimados por sesión para VyOps.

Mantiene el historial de operaciones de una sesión de forma aislada.
Los importes se expresan en dólares estadounidenses (USD).

Este módulo proporciona un mecanismo sencillo para registrar
y consultar los costos estimados de las operaciones
realizadas durante una sesión de VyOps.

Responsabilidades principales:

    1. Inicializar un registro de costos vacío.
    2. Validar los importes antes de registrarlos.
    3. Almacenar los costos de operaciones exitosas.
    4. Calcular el costo acumulado de una sesión.
    5. Proporcionar una copia del historial de costos.

Reglas de validación:

    - Se aceptan valores numéricos int y float.
    - No se aceptan valores booleanos.
    - No se aceptan importes negativos.
    - No se aceptan valores infinitos.
    - No se aceptan valores NaN.
    - Se permite registrar un costo igual a cero.

Precisión numérica:

    El cálculo del total utiliza math.fsum()
    para reducir los errores de redondeo
    que pueden aparecer al sumar valores flotantes.

Aislamiento:

    Cada instancia de RegistroCostosSesion mantiene
    su propia lista de operaciones.

    El módulo no implementa un registro global
    ni comparte automáticamente los costos
    entre distintas instancias.

IMPORTANTE:
    Los costos son estimaciones expresadas en USD.

    Este módulo no consulta tarifas de proveedores,
    no calcula automáticamente el consumo de tokens
    y no realiza cobros reales.

    El almacenamiento se mantiene en memoria
    mientras exista la instancia correspondiente.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# math proporciona:
#
# isfinite():
#     Permite comprobar que un valor numérico
#     no sea infinito ni NaN.
#
# fsum():
#     Realiza sumas de valores flotantes
#     con mayor precisión que una suma convencional.
import math


# ============================================================
# 2. REGISTRO DE COSTOS POR SESIÓN
# ============================================================

class RegistroCostosSesion:
    """Acumula los costos estimados de una sesión.

    Cada instancia mantiene una colección independiente
    de los importes correspondientes a sus operaciones.

    Los valores se almacenan como números flotantes
    y representan costos estimados en USD.

    Attributes:
        _operaciones:
            Lista interna que contiene los costos
            de las operaciones registradas.

    Métodos disponibles:

        registrar_operacion():
            Valida y almacena un costo individual.

        obtener_total():
            Calcula el costo acumulado de la sesión.

        obtener_operaciones():
            Devuelve una copia de los importes registrados.

    La clase no utiliza almacenamiento persistente.

    El aislamiento entre sesiones depende
    de utilizar instancias independientes.
    """

    # --------------------------------------------------------
    # 2.1. INICIALIZACIÓN DEL REGISTRO
    # --------------------------------------------------------

    def __init__(self):
        """Inicializa una sesión sin operaciones registradas.

        Crea una lista vacía destinada a almacenar
        los costos estimados de las operaciones.

        Cada instancia obtiene su propia lista.

        No se registran costos iniciales
        ni se cargan operaciones anteriores.
        """

        # Lista privada de importes registrados.
        #
        # Cada elemento representará el costo estimado
        # de una operación expresado en USD.
        self._operaciones = []

    # --------------------------------------------------------
    # 2.2. REGISTRO DE UNA OPERACIÓN
    # --------------------------------------------------------

    def registrar_operacion(self, costo_usd: float) -> None:
        """Registra el costo estimado de una operación exitosa.

        Args:
            costo_usd:
                Importe estimado de la operación
                expresado en dólares estadounidenses.

                Debe ser un número finito no negativo.

        Raises:
            ValueError:
                Cuando el costo:

                - Es un valor booleano.
                - No pertenece a los tipos int o float.
                - Es infinito.
                - Es NaN.
                - Es negativo.

        Los importes válidos se convierten a float
        antes de incorporarlos al registro.

        Un costo de 0.0 es válido.

        La función no devuelve ningún valor.

        La condición de operación exitosa debe ser
        determinada por el componente que invoca
        este método.
        """

        # ----------------------------------------------------
        # 2.3. VALIDACIÓN DEL IMPORTE
        # ----------------------------------------------------

        # Verifica que el valor recibido cumpla
        # todas las condiciones requeridas.
        #
        # La validación rechaza expresamente los booleanos
        # porque bool es una subclase de int en Python.
        #
        # También comprueba que el valor sea numérico,
        # finito y mayor o igual a cero.
        if (
            isinstance(costo_usd, bool)
            or not isinstance(costo_usd, (int, float))
            or not math.isfinite(costo_usd)
            or costo_usd < 0
        ):
            # Impide incorporar un costo inválido
            # al historial de la sesión.
            raise ValueError(
                "El costo debe ser un número finito no negativo."
            )

        # ----------------------------------------------------
        # 2.4. ALMACENAMIENTO DEL COSTO
        # ----------------------------------------------------

        # Convierte el importe validado a float
        # y lo agrega al final de la lista.
        #
        # Las operaciones anteriores se conservan.
        self._operaciones.append(float(costo_usd))

    # --------------------------------------------------------
    # 2.5. CÁLCULO DEL COSTO ACUMULADO
    # --------------------------------------------------------

    def obtener_total(self) -> float:
        """Devuelve el costo acumulado de la sesión en USD.

        Returns:
            float:
                Suma de todos los costos registrados.

                Si no existen operaciones,
                devuelve 0.0.

        Utiliza math.fsum() para reducir
        los errores de redondeo durante
        la acumulación de valores flotantes.

        Esta operación no modifica
        el historial de costos.
        """

        # Suma todos los importes almacenados.
        #
        # fsum() proporciona una acumulación
        # numéricamente más precisa.
        return math.fsum(self._operaciones)

    # --------------------------------------------------------
    # 2.6. CONSULTA DEL HISTORIAL DE OPERACIONES
    # --------------------------------------------------------

    def obtener_operaciones(self) -> list[float]:
        """Devuelve una copia de los costos registrados.

        Returns:
            list[float]:
                Lista independiente que contiene
                los costos de las operaciones
                en su orden de registro.

                Si no existen operaciones,
                devuelve una lista vacía.

        Se utiliza list.copy() para evitar
        entregar directamente la lista interna.

        Modificar la lista devuelta no altera
        el historial almacenado en la instancia.

        Esta operación no modifica
        el costo acumulado de la sesión.
        """

        # Devuelve una copia superficial de la lista.
        #
        # Como los elementos son números flotantes,
        # la copia permite consultar y modificar
        # la colección devuelta sin alterar
        # la lista interna del registro.
        return self._operaciones.copy()
