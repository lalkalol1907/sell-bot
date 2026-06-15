# frozen_string_literal: true

generated = Rails.root.join("lib/grpc/generated")
$LOAD_PATH.unshift(generated.to_s) unless $LOAD_PATH.include?(generated.to_s)

Dir[generated.join("*_pb.rb")]
  .reject { |path| path.include?("_services_pb") }
  .sort
  .each { |file| require file }

Dir[generated.join("*_services_pb.rb")].sort.each { |file| require file }
