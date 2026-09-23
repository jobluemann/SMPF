<?php
/**
 * SMPF API Client
 *
 * Handles all REST communication between WordPress and the FastAPI backend.
 *
 * @package SMPF_Core
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Class SMPF_API_Client
 */
class SMPF_API_Client {

    /**
     * Base URL of the FastAPI backend.
     *
     * @var string
     */
    private $base_url;

    /**
     * API key for authentication (if set).
     *
     * @var string
     */
    private $api_key;

    /**
     * Request timeout in seconds.
     *
     * @var int
     */
    private $timeout = 15;

    /**
     * Constructor.
     */
    public function __construct() {
        $this->base_url = rtrim( get_option( 'smpf_backend_url', 'http://127.0.0.1:8000' ), '/' );
        $this->api_key  = get_option( 'smpf_api_key', '' );
    }

    /**
     * Perform a GET request.
     *
     * @param string $endpoint API endpoint (e.g. '/api/analytics/overview').
     * @param array  $params   Optional query parameters.
     * @return array|WP_Error
     */
    public function get( $endpoint, $params = array() ) {
        $url = $this->base_url . $endpoint;
        if ( ! empty( $params ) ) {
            $url = add_query_arg( $params, $url );
        }
        return $this->request( 'GET', $url );
    }

    /**
     * Perform a POST request.
     *
     * @param string $endpoint API endpoint.
     * @param array  $body     Request body data.
     * @return array|WP_Error
     */
    public function post( $endpoint, $body = array() ) {
        $url = $this->base_url . $endpoint;
        return $this->request( 'POST', $url, $body );
    }

    /**
     * Perform a DELETE request.
     *
     * @param string $endpoint API endpoint.
     * @return array|WP_Error
     */
    public function delete( $endpoint ) {
        $url = $this->base_url . $endpoint;
        return $this->request( 'DELETE', $url );
    }

    /**
     * Generic HTTP request handler.
     *
     * @param string $method HTTP method.
     * @param string $url    Full URL.
     * @param array  $body   Optional body for POST.
     * @return array|WP_Error
     */
    private function request( $method, $url, $body = null ) {
        $headers = array(
            'Accept'       => 'application/json',
            'Content-Type' => 'application/json',
        );
        if ( ! empty( $this->api_key ) ) {
            $headers['X-API-Key'] = $this->api_key;
        }

        $args = array(
            'method'  => $method,
            'headers' => $headers,
            'timeout' => $this->timeout,
            'sslverify' => false, // Internal/backend call — adjust for production.
        );

        if ( null !== $body ) {
            $args['body'] = wp_json_encode( $body );
        }

        $response = wp_remote_request( $url, $args );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $status = wp_remote_retrieve_response_code( $response );
        $data   = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( $status < 200 || $status >= 300 ) {
            $error_msg = isset( $data['detail'] ) ? $data['detail'] : __( 'Backend returned an error.', 'smpf-core' );
            return new WP_Error( 'smpf_api_error', $error_msg, array( 'status' => $status ) );
        }

        return $data;
    }

    /**
     * Check if the backend is reachable.
     *
     * @return bool
     */
    public function is_backend_online() {
        $result = $this->get( '/' );
        return ! is_wp_error( $result );
    }
}
