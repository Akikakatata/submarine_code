require 'json'
require 'socket'
require 'optparse'

# Your classes and modules

def main
  # Parse command line options
  options = parse_options

  # Create a TCP server
  server = TCPServer.new(options[:host], options[:port])
  puts "Server started on #{options[:host]}:#{options[:port]}"

  # Wait for two players to connect
  players = []
  2.times do
    player = server.accept
    players << player
    puts "Player connected: #{player}"
  end

  # Initialize the game server
  json1 = players[0].gets.chomp
  json2 = players[1].gets.chomp
  game_server = Server.new(json1, json2)

  # Send initial conditions to players
  players.each_with_index do |player, index|
    initial_conditions = game_server.initial_condition(index)
    player.puts(initial_conditions[index])
  end

  # Main game loop
  active_player = 0
  while true
    active_player_socket = players[active_player]
    passive_player_socket = players[1 - active_player]

    # Get action from the active player
    action = active_player_socket.gets.chomp

    # Process the action and get the results
    results = game_server.action(active_player, action)
    Reporter.report_field(results, active_player) unless $VERBOSE.nil?

    # Send results to the active player
    active_player_socket.puts(results[active_player])

    # Send results to the passive player
    passive_player_socket.puts(results[1 - active_player])

    # Check for game over
    break if results[active_player].include?('outcome')

    # Switch active and passive players
    active_player = 1 - active_player
  end

  # Close the server and player connections
  server.close
  players.each(&:close)
end

# Helper method to parse command line options
def parse_options
  options = {
    host: 'localhost',
    port: 5000
  }

  OptionParser.new do |opts|
    opts.banner = 'Usage: server.rb [options]'

    opts.on('-h', '--host HOST', 'Host (default: localhost)') do |host|
      options[:host] = host
    end

    opts.on('-p', '--port PORT', 'Port (default: 5000)') do |port|
      options[:port] = port.to_i
    end
  end.parse!

  options
end

# Run the main method
main
