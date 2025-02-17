# Use an official Node.js runtime as a parent image
FROM node:18 as build

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the React application
RUN npm run build

# Install a lightweight static file server
RUN npm install -g serve

# Serve the build folder on port 8080 (required for Google Cloud Run)
CMD ["serve", "-s", "build", "-l", "8080"]

# Expose port 8080
EXPOSE 8080