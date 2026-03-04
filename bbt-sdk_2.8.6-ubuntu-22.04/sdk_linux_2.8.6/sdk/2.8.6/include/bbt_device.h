#ifndef BBT_DEVICE_H
#define BBT_DEVICE_H

/**
  @file
  @brief Header for the Bitbrain device SDK

This file contains the C interface to the Bitbrain device SDK.

  @bug No known bugs

  @date
  @showdate "%d-%m-%Y"
*/

/**
 * @mainpage SDK for Bitbrain devices
 *
 * This SDK lets you interact with any individual Bitbrain device through a common interface.
 * All the functions are defined in a single header file @ref bbt_device.h.
 *
 * You can check the functionality of the SDK by [topic](topics.html).
 *
 * Download the last version of the library and runtime dependencies for your OS and architecture from the [download center](https://downloads.bitbrain.com/products/software/sdk-c).
 *
 * You can find examples on the use of this SDK in [this repository](https://gitlab.com/bitbrain-public/sdk).
 *
 * > [!NOTE]
 * >
 * > Python SDK is no longer released with the C SDK.
 * > This decission has been made to avoid dealing with multiple python versions and their compatibility problems.
 * > Instead, we propose here different options to easily use this C SDK from python:
 * >  - [swig](https://www.swig.org/)
 * >  - [CFFI](https://cffi.readthedocs.io/en/stable/index.html)
 * >  - [ctypes](https://docs.python.org/3/library/ctypes.html)
 * >
 * > Find [here](https://realpython.com/python-bindings-overview/) a very complete post about these and other options to access the SDK from python with their pros and cons.
 *
 * For any problem with this SDK you can contact us through support@bitbrain.com.
 *
 */


#ifdef WIN32
#ifdef BBT_SDK_STATIC_DEFINE
#  define BBT_SDK_API
#  define BBT_SDK_NO_EXPORT
#else
#  ifndef BBT_SDK_API
#    ifdef BBT_SDK_EXPORTS
/* We are building this library */
#      define BBT_SDK_API __declspec(dllexport)
#    else
/* We are using this library */
#      define BBT_SDK_API __declspec(dllimport)
#    endif
#  endif

#  ifndef BBT_SDK_NO_EXPORT
#    define BBT_SDK_NO_EXPORT
#  endif
#endif
#else
#  define BBT_SDK_API
#endif

#ifndef BBT_SDK_DEPRECATED
#  define BBT_SDK_DEPRECATED __declspec(deprecated)
#endif

#ifndef BBT_SDK_DEPRECATED_EXPORT
#  define BBT_SDK_DEPRECATED_EXPORT BBT_SDK_API BBT_SDK_DEPRECATED
#endif

#ifndef BBT_SDK_DEPRECATED_NO_EXPORT
#  define BBT_SDK_DEPRECATED_NO_EXPORT BBT_SDK_NO_EXPORT BBT_SDK_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef BBT_SDK_NO_DEPRECATED
#    define BBT_SDK_NO_DEPRECATED
#  endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @defgroup bbt_device_lifetime Create and destroy Bitbrain device handlers
 *
 * @brief Constructors and destructors of device handlers
 *
 * The main interaction to a specific device is performed using a handler to it as the first parameter for most of the functions in the SDK.
 * The handler is provided by the *bbt_device_new_* family of functions.
 * These functions initialize the data to interact to a given device and return a handler to use infuture SDK calls to act on the specific device.
 * The handler must be kept as long as it lasts the interaction to the specific device.
 * There is no need to generate a new handler upon disconnections or reconnections. In other words, the handler to a device outlives the connection to it.
 *
 * > [!IMPORTANT]
 * > The call to @ref bbt_device_free is **mandatory** to properly finish the device handler. Otherwise, memory leaks might be caused.
 */

/**
 * @ingroup bbt_device_lifetime
 * @brief bbt_device_t is an opaque type that identifies a connection to a device
 *
 * It is used along the SDK to identify the device to interact to.
 */
typedef struct bbt_device_s bbt_device_t;

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to an air type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_air(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a diadem type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_diadem(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a hero type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_hero(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a 8-channels versatile type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_versatile_8(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a 16-channels versatile type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_versatile_16(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a 32-channels versatile type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_versatile_32(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a 64-channels versatile type device
 * @param left_device_name The name of the device on the left of the setup
 * @param right_device_name The name of the device on the right of the setup
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_versatile_64(const char* left_device_name, const char* right_device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a biosignal versatile type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_versatile_bio(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a ring type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_ring(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to an ikon type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_ikon(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Creates an instance of a handler to a ikon-sleep versatile type device
 * @param device_name The name of the device to interact to as written in the label
 * @return On success, a pointer to the opaque structure. On failure, NULL is returned
 */
BBT_SDK_API bbt_device_t* bbt_device_new_ikon_sleep(const char* device_name);

/**
 * @ingroup bbt_device_lifetime
 * @brief Destroys the handler to a device
 * @param device The handler to the device
 */
BBT_SDK_API void bbt_device_free(bbt_device_t* device);

/**
 * @defgroup connection_management Manage the connection to the device
 *
 * @brief Functions to manage the status of the connection to the device
 *
 * Connnections to Bitbrain devices are managed by processes that run in the background.
 * The rationale behind this decission is to be able to manage multiple connections coordinately.
 * The functions in this SDK interact with the servers to communicate with the devices through them.
 * So, in order to communicate with the devices, the servers must be running as long as any connection is active.
 * Thus, make sure that you start them before any call to @ref bbt_device_connect is performed.
 * After all the devices are disconnected, servers can be safely killed.
 *
 * > [!IMPORTANT]
 * > A single set of connection servers are required per machine.
 * > If you plan to have multiple programs connecting to multiple devices, only a single call to @ref bbt_device_run_connection_server is needed.
 *
 * Wireless connections can fail if the conditions are not optimal.
 * A failure in the connection will provoke a failure in most of the other functions, as a connection is required to communicate to the device.
 * After a failure in one of the calls, it is important to check the connection status and reconnect if needed (check @ref bbt_device_reconnect).
 * The status of the connection to a Bitbrain device does not change the state of the device acquisition, it just breaks the data stream comming and going.
 * So, if a device was configured, the configuration keeps the same after a reconnection.
 * During acquisition, a disconnection may cause data loss in the live stream of data.
 * But if the SD card is enabled, all the data keeps being recorded in the device even during disconnections.
 */

/**
 * @ingroup connection_management
 * @brief Starts the servers needed to stablish the connections to the devices.
 *
 * This servers are mandatory to have a successful connection. Run this function before any call to bbt_device_connect.
 *
 * @param connection_server_folder The folder where the execuables (bthserver and bbt-connection-server) are in the hard drive
 * @return True on successful launch of the servers. False otherwise.
 */
BBT_SDK_API int bbt_device_run_connection_server(const char *connection_server_folder);

/**
 * @ingroup connection_management
 *
 * @brief Kills the connection servers
 * @return True on success. False otherwise
 */
BBT_SDK_API int bbt_device_kill_connection_server();

/**
 * @ingroup connection_management
 *
 * @brief Initiates the connection to the device
 * @param device The handler to the device
 * @return True on success
 */
BBT_SDK_API int bbt_device_connect(bbt_device_t* device);

/**
 * @ingroup connection_management
 * @brief Disconnects from the device and clears the information from the device.
 *
 * Use this function to make a full disconnection to the device. To solve accidental disconnections, use @ref bbt_device_reconnect.
 *
 * @param device The handler to the device
 * @return  True on success
 */
BBT_SDK_API int bbt_device_disconnect(bbt_device_t* device);

/**
 * @ingroup connection_management
 * @brief Recovers from accidental disconnection
 *
 * This function will reconnect the device, keeping all the configurations.
 *
 * @param device The handler to the device
 * @return True on success
 */
BBT_SDK_API int bbt_device_reconnect(bbt_device_t* device);

/**
 * @ingroup connection_management
 * @brief Returns the state of the connection with the device
 * @param device The handle to the device
 * @return True if connected, false othersiwe.
 */
BBT_SDK_API int bbt_device_is_connected(const bbt_device_t* device);

/**
 * @defgroup device_configuration Configure the device
 *
 * @brief Functions to query and change the device cnfiguration
 *
 * The initial state of a device after a reset is the configuration mode with all the signals disabled and the SD Card recording disabled too.
 * You can query and modify the configuration of the device by calling the functions in this group.
 * During configuration, no data streaming is available.
 * Only a request/reply communication happens between the SDK and the device.
 *
 */

/**
 * @ingroup device_configuration
 *
 * @brief Gets the major and minor versions of the device hardware
 * @param device The handle to the device
 * @param major The number of major version
 * @param minor The number of minor version
 * @return True on success, false otherwise.
 */
BBT_SDK_API int bbt_device_get_hardware_version(const bbt_device_t* device, unsigned short* major,unsigned short* minor);

/**
 * @ingroup device_configuration
 * @brief Gets the major and minor versions of the device firmware
 * @param device The handle to the device
 * @param major The number of major version
 * @param minor The number of minor version
 * @return True on success, false otherwise.
 */
BBT_SDK_API int bbt_device_get_firmware_version(const bbt_device_t* device, unsigned short* major, unsigned short* minor);

/**
 * @ingroup device_configuration
 *
 * @brief Returns the frequency that the device communicates new data when acquiring
 *
 * On acquisition, you should call @ref bbt_device_read at this frequency to avoid data loss
 *
 * @param device The handle to the device
 * @return The frequency value in Hz. 0 If something went wrong.
 */
BBT_SDK_API unsigned short bbt_device_get_frequency(const bbt_device_t* device);

/**
 * @ingroup device_configuration
 *
 * @brief The bbt_device_signal_type_t enum
 *
 * This enum identifies the types of signals that the devices from Bitbrain can acquire
 */
enum bbt_device_signal_type_t {
    Accelerometer = 0,
    Analog_Aux,
    BVP,
    Digital_Aux,
    Digital_Input,
    Digital_Output,
    EEG,
    EXG,
    GSR,
    IMU,
    Photodiode,
    PPG,
};

/**
 * @ingroup device_configuration
 *
 * @brief The bbt_device_signal_t class
 *
 * This struct contains the information of each of the signals that a device may provide
 */
struct bbt_device_signal_t
{
    /** The type of signal */
    enum bbt_device_signal_type_t type;

    /** The number of channels */
    unsigned short channels;

    /** The samples per channel in each block received on every @ref bbt_device_read call */
    unsigned short samples_in_block;

    /** The sampling rate (Hz) of the signal */
    unsigned short sampling_rate;
};

/**
 * @ingroup device_configuration
 * @brief Get the list of signals available in the device
 *
 * The order of the list is crucial to be able to index the data received during acquisition with @ref bbt_device_read.
 *
 * @param device The handle to the device
 * @param n Output parameter to receive the number of signals 0 <= n <= 10.
 * @param device_signals Output parameter to receive the array of pointers to bbt_device_signal_t. The index in this array will be used to identify the signal in the device in other functions.
 * @return True on success. False otherwise
 */
BBT_SDK_API int bbt_device_get_signals(const bbt_device_t* device, unsigned short* n, const struct bbt_device_signal_t **device_signals);

/**
 * @ingroup device_configuration
 *
 * @brief Gets the configuration mode of a signal in the device
 * @param device The handle of the device
 * @param n The index of the signal as returned in the @ref bbt_device_get_signals function.
 * @return The mode of the signal. 0 if it is disabled (not aquired). Values different from 0 indicate that the signal is being acquired.
 */
BBT_SDK_API int bbt_device_get_signal_mode(const bbt_device_t* device, unsigned short n);

/**
 * @ingroup device_configuration
 *
 * @brief Enables the acquisition of this signal
 * @param device The handle to the device
 * @param n The index of the signal to enable, as returned in the array from function @ref bbt_device_get_signals
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_enable_signal(bbt_device_t* device, unsigned short n);

/**
 * @ingroup device_configuration
 *
 * @brief Disables the acquisition of this signal
 * @param deviceThe handle to the device
 * @param n The index of the signal to disable, as returned in the array from function @ref bbt_device_get_signals
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_disable_signal(bbt_device_t* device, unsigned short n);

/**
 *
 * @ingroup device_configuration
 *
 * @brief Sets the mode to a specific value
 *
 * > [!NOTE]
 * > This function is not needed in general, as the signals can be enabled/disabled using the corresponding functions.
 * > Only very specific uses of specific signals may require this function.
 *
 * @param device The handle to the device
 * @param n The index of the signal to set the mode, as returned in the array from function @ref bbt_device_get_signals
 * @param mode The mode to set. Acceptable values are from 0 to 255. A value of 0 disables the signal.
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_set_signal_mode(bbt_device_t* device, unsigned short n, int mode);

/**
 * @ingroup device_configuration
 *
 * @brief Check if the device has SD Card capabilities to record the data
 * @param device The handle to the device
 * @return True if the device can record data in the SD Card. False otherwise.
 */
BBT_SDK_API int bbt_device_has_sd_card_capabilities(const bbt_device_t* device);

/**
 * @ingroup device_configuration
 *
 * @brief Check if the SD Card recording is enabled in the device
 * @param device The handle to the device
 * @return True if the recording to the SD card is enabled. False otherwise
 */
BBT_SDK_API int bbt_device_is_sd_card_enabled(const bbt_device_t* device);

/**
 * @ingroup device_configuration
 *
 * @brief Enable the SD Card recording in the device
 * @param device The handle to the device
 * @param full_recording_path The path in the SD Card where the recording will take place
 * @return True on success. False otherwise
 */
BBT_SDK_API int bbt_device_enable_sd_card(bbt_device_t* device, const char* full_recording_path);

/**
 * @ingroup device_configuration
 *
 * @brief Disable the SD Card recording  in the device
 * @param device The handle to the device
 * @return True on success. False otherwise
 */
BBT_SDK_API int bbt_device_disable_sd_card(bbt_device_t* device);

/**
 * @defgroup acquisition Data acquisition
 *
 * @brief Data acquisition and recording functions
 *
 * These functions manage the acquisition of the dats from the device.
 * From configuration state, you can enter into acquisition state bt running @ref bbt_device_start.
 * To stop the acquisition and return to configuration state, call @ref bbt_device_stop.
 *
 * In acquisition state, the only accepted commands to the device are @ref bbt_device_read and @ref bbt_device_stop.
 * No commands in the configuration group @ref device_configuration are available.
 *
 * Regarding connection, you can manage the connection/disconnection of the device during acquisition with @ref bbt_device_is_connected and @ref bbt_device_reconnect.
 *
 */

/**
 * @ingroup acquisition
 *
 * @brief Sets the device into acquisition mode
 *
 * The device enters into acquisition mode and starts streaming signals to the SDK that must be read with @ref bbt_device_read and recording data into the SD Card if configured
 *
 * @param device The handler to the device
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_start(bbt_device_t* device);

/**
 * @ingroup acquisition
 *
 * @brief Stops acquisition mode and enters configuration mode
 *
 * The device enters into aconfiguration mode and stop streaming signals and recording into SD Card.
 *
 * @param device The handler to the device
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_stop(bbt_device_t* device);

/**
 * @ingroup acquisition
 *
 * @brief Checks if the device is in acquisition mode
 * @param device The handler to the device
 * @return True if in acquisition mode. False otherwise
 */
BBT_SDK_API int bbt_device_is_acquiring(const bbt_device_t* device);

/**
 * @ingroup acquisition
 *
 * @defgroup battery_levels Battery level constants
  *
 * @brief Possible values for the battery field in @ref bbt_device_data_block_t
 *
 * Values from 0 to 5 indicate the level of battery in percentage from 0 = 0%
 * to 5 = 100%.
 * Other possible values are @ref bbt_device_battery_unknown, when the level is being computed, and @ref
 * bbt_device_battery_charging when the device is connected to the charger.
 *
 *@{
*/

BBT_SDK_API extern const short bbt_device_battery_unknown; /**  The battery level is not known yet. */
BBT_SDK_API extern const short bbt_device_battery_charging; /**  The charger is connected. */
/**
 * @}
 */

/**
 * @ingroup acquisition
 *
 * @defgroup impedance_values EEG impedance/quality values
 *
 * @brief Possible values for the impedance/quality of each channel of EEG
 *
 * This is an estimation based on a relative impedance measurement among channels at a frequency out of the working EEG band to avoid noise into the channel.
 *
 * 5 Different values are possible: from @ref bbt_device_impedance_unknown to @ref bbt_device_impedance_good.
 * For good EEG mesurements, correct the sensors setup until values @ref bbt_device_impedance_good or else @ref bbt_device_impedance_fair are obtained
 * @{
 */
/**
 * @brief The impedance/quality is being computed
 */
BBT_SDK_API extern const unsigned short bbt_device_impedance_unknown;
/**
 * @brief The channel is saturated
 */
BBT_SDK_API extern const unsigned short bbt_device_impedance_saturated;
/**
 * @brief The impedance/quality of the channel is bad
 */
BBT_SDK_API extern const unsigned short bbt_device_impedance_bad;
/**
 * @brief The impedance/quality of the channel is fair
 */
BBT_SDK_API extern const unsigned short bbt_device_impedance_fair;
/**
 * @brief The impedance/quality of the channel is good
 */
BBT_SDK_API extern const unsigned short bbt_device_impedance_good;

/**@}*/


/**
 * @ingroup acquisition
 *
 * @brief The bbt_device_data_block_t class
 *
 * A device data block is generated and communicated at a fixed frequency (@ref bbt_device_get_frequency) by the device.
 * Each block contains a unique[1] consecutive sequence, the battery level, a flag that inidicates any problem and the data from the differrent signals.
*
 * The data is separated per signal. So, the data of the signal with index i in the device_signals array obtained from @ref bbt_device_get_signals, is in the signal_data[i] array of doubles.
 * Inside each signal data array, the values are arranged in a channels x samples matrix, as is the @ref bbt_device_signal_t struct. First, all the samples from channel 1, then all the samples from channel 2, etc.
 * If the signal is not enabled, the pointer to the data of the signal is set to 0.
 * If an eeg signal is returned, the corresponding contact impedance/quality measurement is available in the impedances field.
 *
 * [1] The sequence wraps after 2^16 data blocks and goes back to 0 again.
 *
 */
struct bbt_device_data_block_t
{
    /** The number of sequence of the data block. They are consecutive and wrap around at 2**16 */
    unsigned short sequence;

    /** The remaining battery (see @ref battery_levels) */
    short battery;

    /** A flag set inidicating any problem during acquisition. 0 if no problem occur */
    unsigned short flags;

    /** The table of data per signal */
    double* signal_data[10];

    /** If EEG is being acquired, this list is the quality per channel (see @ref impedance_values)*/
    unsigned short* impedances;
};


/**
 * @ingroup acquisition
 *
 * @brief Read a data block from a device
 *
 * Fills the block data structure with the last information from the device
 *
 * @param device The handler to the device
 * @param block Output parameter to hold the information read
 * @return True on success, false otherwise
 */
BBT_SDK_API int bbt_device_read(bbt_device_t* device, struct bbt_device_data_block_t* block);


#ifdef __cplusplus
}
#endif


#endif // BBT_DEVICE_H
